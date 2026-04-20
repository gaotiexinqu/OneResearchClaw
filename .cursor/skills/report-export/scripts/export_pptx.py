from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class PPTXExportError(RuntimeError):
    pass


def export_pptx(input_report: Path, output_dir: Path, output_lang: str = "en") -> Path:
    script_dir = Path(__file__).resolve().parent
    planner_path = script_dir / "plan_slides.py"
    renderer_path = script_dir / "export_pptx.js"

    node = shutil.which("node")
    if not node:
        raise PPTXExportError("Could not find node in PATH for PPTX export.")

    # output_dir is base_dir/format when called from export_report.py
    # -> strip /format, add /output_lang/format to get base_dir/lang/format
    final_dir = output_dir.parent / output_lang / output_dir.name
    final_dir.mkdir(parents=True, exist_ok=True)
    output_path = final_dir / "report.pptx"

    with tempfile.TemporaryDirectory(prefix="report_export_pptx_") as tmp_dir:
        slide_plan_path = Path(tmp_dir) / "slide_plan.json"

        planner_cmd = [
            sys.executable,
            str(planner_path),
            str(input_report),
            str(slide_plan_path),
        ]
        planner_proc = subprocess.run(planner_cmd, capture_output=True, text=True)
        if planner_proc.returncode != 0:
            raise PPTXExportError(
                f"Slide planning failed with code {planner_proc.returncode}.\n"
                f"STDOUT:\n{planner_proc.stdout}\n"
                f"STDERR:\n{planner_proc.stderr}"
            )

        if not slide_plan_path.exists() or slide_plan_path.stat().st_size == 0:
            raise PPTXExportError("Slide planning did not produce a non-empty slide_plan.json file.")

        render_cmd = [node, str(renderer_path), str(slide_plan_path), str(output_path)]
        render_proc = subprocess.run(render_cmd, capture_output=True, text=True)
        if render_proc.returncode != 0:
            raise PPTXExportError(
                f"PPTX export failed with code {render_proc.returncode}.\n"
                f"STDOUT:\n{render_proc.stdout}\n"
                f"STDERR:\n{render_proc.stderr}"
            )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise PPTXExportError("PPTX export did not produce a non-empty .pptx file.")

    return output_path
