#!/usr/bin/env python3
"""Create a completely synthetic workbook for tests and public demos."""

from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import Workbook


HEADERS = ["整改单号", "区域", "项目", "检查类型", "整改单状态", "品质检查任务名称", "检查方式", "问题描述", "所属板块", "检查维度", "检查标准", "扣罚分值", "整改措施", "实施描述", "提交人", "提交时间"]


def create_sample(path: Path, multi_project: bool = False, filename_mismatch: bool = False) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "品质整改明细"
    sheet.append(["品质检查"])
    sheet.append(HEADERS)
    boards = ["环境服务", "工程服务", "秩序服务", "综合管理", "客户服务"]
    rows = [
        ("已整改", "公共区域积尘", 1.0),
        ("已整改", "设备巡检记录缺失", 2.0),
        ("待整改", "门禁设备离线", 5.0),
        ("待整改", "车位堆放杂物", 0.0),
        ("已整改", "无", 0.0),
        ("已整改", "消防卷帘卫生需改善", 0.2),
        ("已整改", "供方资料不完整", 1.0),
        ("待整改", "健身设施损坏", 0.5),
        ("已整改", "楼道照明故障", 0.3),
        ("已整改", "客户拜访记录缺失", 1.0),
    ]
    for index, (status, problem, score) in enumerate(rows, 1):
        project = "合成花园" if not multi_project or index <= 5 else "合成公馆"
        sheet.append([
            f"SYN-{index:04d}", "示例区域", project, "合成检查", status,
            "月度品质检查" if index <= 5 else "专项品质检查", "线下", problem,
            boards[(index - 1) % len(boards)], f"合成检查维度-{index}", "合成标准", score,
            "合成整改措施", "合成实施描述" if status == "已整改" else "", f"测试人员-{(index%3)+1}",
            f"2026-07-{24 if index <= 5 else 29:02d} 10:{index:02d}:00",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--multi-project", action="store_true")
    args = parser.parse_args(argv)
    create_sample(Path(args.out), args.multi_project)
    print(Path(args.out).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
