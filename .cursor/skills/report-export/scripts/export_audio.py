from __future__ import annotations

import contextlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Iterable, List, Optional

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:
    import soundfile as sf  # type: ignore
except Exception:  # pragma: no cover
    sf = None  # type: ignore

try:
    from kokoro import KPipeline  # type: ignore
except Exception:  # pragma: no cover
    KPipeline = None  # type: ignore


class AudioExportError(RuntimeError):
    pass


def _warn(message: str) -> None:
    print(f"[report-export/audio] {message}", file=sys.stderr)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        _warn(f"Invalid integer for {name}={raw!r}; falling back to {default}.")
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        _warn(f"Invalid float for {name}={raw!r}; falling back to {default}.")
        return default


def _load_markdown(input_report: Path) -> str:
    return input_report.read_text(encoding="utf-8")


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?<!\*)\*(?!\*)", "", text)
    text = text.replace("_", " ")
    text = re.sub(r"\[(?:\d+(?:\s*[-,]\s*\d+)*)\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _ensure_sentence_end(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if re.search(r"[.!?;:]$", text):
        return text
    return text + "."


def _table_row_to_sentence(line: str, headers: Optional[list[str]] = None) -> tuple[Optional[str], Optional[list[str]]]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None, headers

    cells = [c.strip() for c in stripped.strip("|").split("|")]
    if not cells:
        return None, headers

    if all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c):
        return None, headers

    cleaned = [_strip_inline_markdown(c) for c in cells if c.strip()]
    if not cleaned:
        return None, headers

    if headers is None:
        return None, cleaned

    pairs = []
    for idx, value in enumerate(cleaned):
        key = headers[idx] if idx < len(headers) else f"Column {idx + 1}"
        if value:
            pairs.append(f"{key}: {value}")
    if not pairs:
        return None, headers
    return _ensure_sentence_end("; ".join(pairs)), headers


_HEADING_LEVEL1_PREFIX = ""
_HEADING_LEVEL2_PREFIX = "Section"


def markdown_to_speech_blocks(md: str) -> List[str]:
    blocks: List[str] = []
    in_code_fence = False
    pending_table_headers: Optional[list[str]] = None

    for raw in md.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if line.startswith("```"):
            in_code_fence = not in_code_fence
            pending_table_headers = None
            continue
        if in_code_fence:
            continue
        if not line:
            pending_table_headers = None
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            pending_table_headers = None
            level = len(heading.group(1))
            title = _strip_inline_markdown(heading.group(2))
            if title:
                if level == 1:
                    blocks.append(_ensure_sentence_end(title))
                else:
                    prefix = _HEADING_LEVEL2_PREFIX if level == 2 else "Subsection"
                    blocks.append(_ensure_sentence_end(f"{prefix}. {title}"))
            continue

        bullet = re.match(r"^[-*+]\s+(.*)$", line)
        if bullet:
            pending_table_headers = None
            text = _strip_inline_markdown(bullet.group(1))
            if text:
                blocks.append(_ensure_sentence_end(text))
            continue

        ordered = re.match(r"^\d+[.)]\s+(.*)$", line)
        if ordered:
            pending_table_headers = None
            text = _strip_inline_markdown(ordered.group(1))
            if text:
                blocks.append(_ensure_sentence_end(text))
            continue

        table_text, pending_table_headers = _table_row_to_sentence(line, pending_table_headers)
        if table_text:
            blocks.append(table_text)
            continue

        text = _strip_inline_markdown(line)
        if text:
            pending_table_headers = None
            # Remove common PPT continuation noise if present in source reports.
            text = re.sub(r"\(cont\.\)", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"\bSPEAKER\d+\b", "Speaker", text)
            text = _ensure_sentence_end(text)
            if text:
                blocks.append(text)

    return [b for b in blocks if b.strip()]


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;:])\s+(?=[A-Z0-9\"'“‘(])")
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[,])\s+(?=[A-Z0-9\"'“‘(])")


def _split_long_sentence(text: str, max_len: int) -> List[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    parts = re.split(r"(?<=[;:])\s+", text)
    if len(parts) > 1:
        out: List[str] = []
        for part in parts:
            out.extend(_split_long_sentence(part, max_len))
        return out

    parts = _CLAUSE_SPLIT_RE.split(text)
    if len(parts) > 1:
        out = []
        cur = ""
        for part in parts:
            piece = part.strip()
            if not piece:
                continue
            candidate = f"{cur}, {piece}" if cur else piece
            if cur and len(candidate) > max_len:
                out.append(_ensure_sentence_end(cur))
                cur = piece
            else:
                cur = candidate
        if cur:
            out.append(_ensure_sentence_end(cur))
        return out

    words = text.split()
    out = []
    cur_words: List[str] = []
    for word in words:
        candidate = " ".join(cur_words + [word])
        if cur_words and len(candidate) > max_len:
            out.append(_ensure_sentence_end(" ".join(cur_words)))
            cur_words = [word]
        else:
            cur_words.append(word)
    if cur_words:
        out.append(_ensure_sentence_end(" ".join(cur_words)))
    return out


def _blocks_to_sentences(blocks: Iterable[str], sentence_max_len: int = 280) -> List[str]:
    sentences: List[str] = []
    for block in blocks:
        piece = block.strip()
        if not piece:
            continue
        for sent in _SENTENCE_SPLIT_RE.split(piece):
            sent = sent.strip()
            if not sent:
                continue
            sentences.extend(_split_long_sentence(_ensure_sentence_end(sent), sentence_max_len))
    return [s for s in sentences if s.strip()]


def _chunk_sentences(sentences: Iterable[str], max_chars: int = 1200) -> List[str]:
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for sentence in sentences:
        piece = sentence.strip()
        if not piece:
            continue
        add_len = len(piece) + (1 if cur else 0)
        if cur and cur_len + add_len > max_chars:
            chunks.append(" ".join(cur))
            cur = []
            cur_len = 0
        cur.append(piece)
        cur_len += add_len
    if cur:
        chunks.append(" ".join(cur))
    if not chunks:
        raise AudioExportError("No speakable content found in the markdown report.")
    return chunks


_ESPEAK_LIKE_VOICE_RE = re.compile(r"^[a-z]{2,3}(?:[-_][a-z0-9]+)*$", re.IGNORECASE)


def _default_voice_for_backend(backend: str) -> str:
    if backend == "kokoro":
        return os.environ.get("REPORT_EXPORT_AUDIO_FALLBACK_VOICE", "af_heart").strip() or "af_heart"
    if backend == "espeak-ng":
        return os.environ.get("REPORT_EXPORT_AUDIO_FALLBACK_VOICE", "en-us").strip() or "en-us"
    if backend == "espeak":
        return os.environ.get("REPORT_EXPORT_AUDIO_FALLBACK_VOICE", "en").strip() or "en"
    return "en"


def _normalize_voice_for_backend(backend: str, voice: str) -> str:
    voice = (voice or "").strip()
    if not voice:
        return _default_voice_for_backend(backend)

    if backend in {"espeak-ng", "espeak"} and not _ESPEAK_LIKE_VOICE_RE.fullmatch(voice):
        fallback = _default_voice_for_backend(backend)
        _warn(
            f"Voice {voice!r} does not look compatible with backend {backend}; "
            f"falling back to {fallback!r}."
        )
        return fallback
    return voice


def _kokoro_available() -> bool:
    return KPipeline is not None and np is not None and sf is not None


def _find_backend() -> str:
    forced = os.environ.get("REPORT_EXPORT_AUDIO_BACKEND", "").strip().lower()
    if forced:
        if forced == "kokoro":
            if not _kokoro_available():
                raise AudioExportError(
                    "Requested audio backend 'kokoro' but required Python packages are missing. "
                    "Install: pip install 'kokoro>=0.9.4' soundfile"
                )
            return "kokoro"
        if forced == "piper" and shutil.which("piper"):
            return "piper"
        if forced == "espeak-ng" and shutil.which("espeak-ng"):
            return "espeak-ng"
        if forced == "espeak" and shutil.which("espeak"):
            return "espeak"
        raise AudioExportError(
            f"Requested audio backend '{forced}' is not available. "
            "Set REPORT_EXPORT_AUDIO_BACKEND to kokoro, piper, espeak-ng, or espeak, or unset it for auto detection."
        )

    if _kokoro_available():
        return "kokoro"
    for candidate in ("piper", "espeak-ng", "espeak"):
        if shutil.which(candidate):
            return candidate
    raise AudioExportError(
        "No supported TTS backend found. Install kokoro, piper, espeak-ng, or espeak, "
        "or set REPORT_EXPORT_AUDIO_BACKEND to an available backend."
    )


def _synthesize_chunk_kokoro(text: str, wav_path: Path) -> None:
    if not _kokoro_available():
        raise AudioExportError(
            "Kokoro backend requested but kokoro/soundfile/numpy is unavailable. "
            "Install: pip install 'kokoro>=0.9.4' soundfile"
        )

    assert KPipeline is not None and np is not None and sf is not None
    lang_code = os.environ.get("REPORT_EXPORT_AUDIO_LANG_CODE", "a").strip() or "a"
    voice = _normalize_voice_for_backend("kokoro", os.environ.get("REPORT_EXPORT_AUDIO_VOICE", "af_heart"))
    speed = _env_float("REPORT_EXPORT_AUDIO_SPEED", 1.0)

    pipeline = KPipeline(lang_code=lang_code)
    try:
        generator = pipeline(text, voice=voice, speed=speed)
    except TypeError:
        generator = pipeline(text, voice=voice)

    audio_parts = []
    for item in generator:
        if not isinstance(item, tuple) or len(item) < 3:
            continue
        audio = item[2]
        if audio is None:
            continue
        audio_np = np.asarray(audio, dtype=np.float32).reshape(-1)
        if audio_np.size:
            audio_parts.append(audio_np)

    if not audio_parts:
        raise AudioExportError("Kokoro did not generate any audio for the chunk.")

    merged = np.concatenate(audio_parts, axis=0)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(wav_path), merged, 24000)


def _run_subprocess(cmd: list[str], *, input_text: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _synthesize_chunk(text: str, wav_path: Path, backend: str) -> None:
    if backend == "kokoro":
        _synthesize_chunk_kokoro(text, wav_path)
        return

    if backend == "piper":
        model = os.environ.get("REPORT_EXPORT_PIPER_MODEL", "").strip()
        if not model:
            raise AudioExportError(
                "piper is available, but REPORT_EXPORT_PIPER_MODEL is not set. Point it to a local .onnx voice model."
            )
        cmd = ["piper", "--model", model, "--output_file", str(wav_path)]
        proc = _run_subprocess(cmd, input_text=text)
    elif backend == "espeak-ng":
        voice = _normalize_voice_for_backend(backend, os.environ.get("REPORT_EXPORT_AUDIO_VOICE", "en-us"))
        rate = str(_env_int("REPORT_EXPORT_AUDIO_RATE", 165))
        cmd = ["espeak-ng", "-v", voice, "-s", rate, "-w", str(wav_path), text]
        proc = _run_subprocess(cmd)
        if proc.returncode != 0 and voice != _default_voice_for_backend(backend):
            fallback_voice = _default_voice_for_backend(backend)
            _warn(f"Backend {backend} failed with voice {voice!r}; retrying with {fallback_voice!r}.")
            cmd = ["espeak-ng", "-v", fallback_voice, "-s", rate, "-w", str(wav_path), text]
            proc = _run_subprocess(cmd)
    elif backend == "espeak":
        voice = _normalize_voice_for_backend(backend, os.environ.get("REPORT_EXPORT_AUDIO_VOICE", "en"))
        rate = str(_env_int("REPORT_EXPORT_AUDIO_RATE", 165))
        cmd = ["espeak", "-v", voice, "-s", rate, "-w", str(wav_path), text]
        proc = _run_subprocess(cmd)
        if proc.returncode != 0 and voice != _default_voice_for_backend(backend):
            fallback_voice = _default_voice_for_backend(backend)
            _warn(f"Backend {backend} failed with voice {voice!r}; retrying with {fallback_voice!r}.")
            cmd = ["espeak", "-v", fallback_voice, "-s", rate, "-w", str(wav_path), text]
            proc = _run_subprocess(cmd)
    else:
        raise AudioExportError(f"Unsupported TTS backend: {backend}")

    if proc.returncode != 0:
        raise AudioExportError(
            f"Audio synthesis failed with backend {backend}.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    if not wav_path.exists() or wav_path.stat().st_size == 0:
        raise AudioExportError(f"Audio backend {backend} did not produce a non-empty wav file: {wav_path}")


def _silence_frames(params: wave._wave_params, duration_ms: int) -> bytes:
    frame_rate = params.framerate
    n_channels = params.nchannels
    sampwidth = params.sampwidth
    n_frames = int(frame_rate * max(duration_ms, 0) / 1000.0)
    return b"\x00" * (n_frames * n_channels * sampwidth)


def _concatenate_wavs(parts: List[Path], output_path: Path, pause_ms: int = 220) -> None:
    if not parts:
        raise AudioExportError("No wav parts were produced for concatenation.")

    with contextlib.closing(wave.open(str(parts[0]), "rb")) as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]

    silence = _silence_frames(params, pause_ms)

    for wav_part in parts[1:]:
        with contextlib.closing(wave.open(str(wav_part), "rb")) as wf:
            other_params = wf.getparams()
            if other_params[:3] != params[:3]:
                raise AudioExportError(
                    "Generated wav parts do not share the same audio parameters; cannot concatenate safely."
                )
            frames.append(silence)
            frames.append(wf.readframes(wf.getnframes()))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.closing(wave.open(str(output_path), "wb")) as out:
        out.setparams(params)
        for blob in frames:
            out.writeframes(blob)


def export_audio(input_report: Path, output_dir: Path, output_lang: str = "en") -> Path:
    # output_dir is base_dir/format when called from export_report.py
    # -> strip /format, add /output_lang to get base_dir/lang
    final_dir = output_dir.parent / output_lang
    final_dir.mkdir(parents=True, exist_ok=True)
    output_path = final_dir / "report.wav"

    md = _load_markdown(input_report)
    speech_blocks = markdown_to_speech_blocks(md)
    sentences = _blocks_to_sentences(speech_blocks, sentence_max_len=_env_int("REPORT_EXPORT_AUDIO_SENTENCE_MAX_CHARS", 280))
    max_chars = _env_int("REPORT_EXPORT_AUDIO_MAX_CHARS", 1200)
    chunks = _chunk_sentences(sentences, max_chars=max_chars)
    backend = _find_backend()
    pause_ms = _env_int("REPORT_EXPORT_AUDIO_PAUSE_MS", 220)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        wav_parts: List[Path] = []
        for idx, chunk in enumerate(chunks):
            wav_path = tmpdir_path / f"part_{idx:03d}.wav"
            _synthesize_chunk(chunk, wav_path, backend)
            wav_parts.append(wav_path)
        _concatenate_wavs(wav_parts, output_path, pause_ms=pause_ms)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise AudioExportError("Audio export did not produce a non-empty .wav file.")

    return output_path
