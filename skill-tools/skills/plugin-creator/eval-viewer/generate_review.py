#!/usr/bin/env python3
"""
Plugin Creator 评估查看器 - 生成 HTML 评估界面

用法：
    python eval-viewer/generate_review.py <工作目录> [--skill-name 名称] [--benchmark 路径]
    python eval-viewer/generate_review.py <工作目录> --static <输出.html>
"""

import json
import sys
import argparse
from pathlib import Path


def generate_review_html(workspace, skill_name="plugin-creator", benchmark_path=None, static_output=None):
    """生成 HTML 评估界面。"""

    # 加载基准数据
    benchmark_data = None
    if benchmark_path and Path(benchmark_path).exists():
        with open(benchmark_path, encoding="utf-8") as f:
            benchmark_data = json.load(f)

    # 从工作目录加载评估数据
    grading_files = list(Path(workspace).rglob("grading.json"))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{skill_name} - 插件评估</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        h2 {{ color: #555; margin: 20px 0 10px; }}
        .tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .tab {{ padding: 10px 20px; background: #ddd; border: none; cursor: pointer; border-radius: 4px 4px 0 0; }}
        .tab.active {{ background: #fff; border-bottom: 2px solid #007bff; }}
        .tab-content {{ display: none; background: #fff; padding: 20px; border-radius: 0 4px 4px 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .tab-content.active {{ display: block; }}
        .eval-item {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
        .eval-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .eval-name {{ font-weight: bold; color: #333; }}
        .eval-status {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; }}
        .status-pass {{ background: #d4edda; color: #155724; }}
        .status-fail {{ background: #f8d7da; color: #721c24; }}
        .prompt {{ background: #f8f9fa; padding: 12px; border-radius: 4px; margin-bottom: 12px; }}
        .prompt-label {{ font-weight: bold; color: #666; font-size: 12px; text-transform: uppercase; }}
        .expectations {{ margin-top: 12px; }}
        .expectation {{ padding: 8px 12px; margin: 4px 0; border-radius: 4px; }}
        .exp-pass {{ background: #d4edda; }}
        .exp-fail {{ background: #f8d7da; }}
        .feedback {{ margin-top: 16px; }}
        .feedback textarea {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; min-height: 80px; }}
        .benchmark {{ background: #fff; padding: 20px; border-radius: 8px; }}
        .benchmark-table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        .benchmark-table th, .benchmark-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .benchmark-table th {{ background: #f8f9fa; font-weight: 600; }}
        .submit {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }}
        .submit:hover {{ background: #0056b3; }}
        .summary {{ background: #e9ecef; padding: 16px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{skill_name} - 插件评估</h1>

        <div class="tabs">
            <button class="tab active" onclick="showTab('outputs')">输出</button>
            <button class="tab" onclick="showTab('benchmark')">基准</button>
        </div>

        <div id="outputs" class="tab-content active">
            <h2>测试输出</h2>
"""

    # 添加评估项
    for i, grading_file in enumerate(grading_files):
        run_dir = grading_file.parent
        eval_name = run_dir.name

        with open(grading_file, encoding="utf-8") as f:
            grading = json.load(f)

        passed = grading.get("summary", {}).get("passed", 0)
        failed = grading.get("summary", {}).get("failed", 0)
        pass_rate = grading.get("summary", {}).get("pass_rate", 0)

        html += f"""
            <div class="eval-item">
                <div class="eval-header">
                    <span class="eval-name">{eval_name}</span>
                    <span class="eval-status status-{"pass" if pass_rate >= 0.8 else "fail"}">
                        {passed}/{passed+failed} 通过 ({pass_rate:.0%})
                    </span>
                </div>
                <div class="expectations">
"""

        for exp in grading.get("expectations", []):
            exp_class = "exp-pass" if exp.get("passed") else "exp-fail"
            html += f"""
                    <div class="expectation {exp_class}">
                        {"✅" if exp.get("passed") else "❌"} {exp.get("text", "")}
                    </div>
"""

        html += """
                </div>
                <div class="feedback">
                    <label>反馈：</label>
                    <textarea id="feedback-{i}" placeholder="你的反馈..."></textarea>
                </div>
            </div>
"""

    html += """
        </div>

        <div id="benchmark" class="tab-content">
            <h2>基准测试结果</h2>
"""

    if benchmark_data:
        with_skill = benchmark_data.get("run_summary", {}).get("with_skill", {})
        without_skill = benchmark_data.get("run_summary", {}).get("without_skill", {})
        delta = benchmark_data.get("run_summary", {}).get("delta", {})

        html += f"""
            <div class="benchmark">
                <table class="benchmark-table">
                    <tr>
                        <th>配置</th>
                        <th>通过率</th>
                        <th>平均时间</th>
                    </tr>
                    <tr>
                        <td><strong>使用 Skill</strong></td>
                        <td>{with_skill.get("pass_rate", {}).get("mean", 0):.1%}</td>
                        <td>{with_skill.get("time_seconds", {}).get("mean", 0):.1f}秒</td>
                    </tr>
                    <tr>
                        <td><strong>不使用 Skill</strong></td>
                        <td>{without_skill.get("pass_rate", {}).get("mean", 0):.1%}</td>
                        <td>{without_skill.get("time_seconds", {}).get("mean", 0):.1f}秒</td>
                    </tr>
                    <tr style="background: #e9ecef;">
                        <td><strong>差异</strong></td>
                        <td>{delta.get("pass_rate", "+0%")}</td>
                        <td>{delta.get("time_seconds", "+0秒")}</td>
                    </tr>
                </table>
            </div>
"""
    else:
        html += "<p>没有基准数据可用。</p>"

    html += """
        </div>

        <button class="submit" onclick="submitFeedback()">提交所有反馈</button>
    </div>

    <script>
        function showTab(tabId) {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            document.querySelector(`[onclick="showTab("${tabId}")"]`).classList.add("active");
            document.getElementById(tabId).classList.add("active");
        }

        function submitFeedback() {
            const feedbacks = [];
            document.querySelectorAll(".eval-item").forEach(item => {
                const name = item.querySelector(".eval-name").textContent;
                const textarea = item.querySelector("textarea");
                feedbacks.push({
                    run_id: name,
                    feedback: textarea ? textarea.value : "",
                    timestamp: new Date().toISOString()
                });
            });

            const data = JSON.stringify({ reviews: feedbacks, status: "complete" }, null, 2);
            const blob = new Blob([data], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "feedback.json";
            a.click();

            alert("反馈已保存到 feedback.json");
        }
    </script>
</body>
</html>
"""

    # 写入输出
    if static_output:
        output_path = Path(static_output)
    else:
        output_path = Path(workspace) / "review.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 评估已生成: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="生成插件评估界面")
    parser.add_argument("workspace", help="工作目录")
    parser.add_argument("--skill-name", default="plugin-creator", help="Skill 名称")
    parser.add_argument("--benchmark", help="benchmark.json 路径")
    parser.add_argument("--static", help="静态 HTML 输出路径")

    args = parser.parse_args()

    generate_review_html(args.workspace, args.skill_name, args.benchmark, args.static)


if __name__ == "__main__":
    main()
