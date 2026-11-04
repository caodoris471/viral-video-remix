"""Install a packaged Jianying desktop draft on Windows.

Package layout:
  安装到剪映.py
  剪映草稿/<draft name>/draft_content.json
  剪映草稿/<draft name>/draft_meta_info.json
  素材/*
"""

import argparse
import copy
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import sys
import time
import uuid


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def select_draft_root(index: dict, override: str | None) -> Path:
    if override:
        root = Path(override)
        if not root.is_dir():
            raise RuntimeError(f"草稿目录不存在：{root}")
        return root.resolve()
    for entry in index.get("all_draft_store", []):
        raw = entry.get("draft_root_path", "")
        if raw and Path(raw).is_dir():
            return Path(raw).resolve()
    raise RuntimeError("找不到剪映草稿目录。请在剪映设置中查看草稿保存位置，并用 --draft-root 指定。")


def install(package: Path, index_file: Path, draft_root_override: str | None = None) -> Path:
    draft_candidates = list((package / "剪映草稿").glob("*/draft_content.json"))
    if len(draft_candidates) != 1:
        raise RuntimeError("安装包中应只有一个 剪映草稿/工程名/draft_content.json")
    source_draft = draft_candidates[0].parent
    source_media = package / "素材"
    if not source_media.is_dir() or not (source_draft / "draft_meta_info.json").is_file():
        raise RuntimeError("安装包缺少素材文件夹或 draft_meta_info.json")
    if not index_file.is_file():
        raise RuntimeError(f"找不到剪映草稿索引：{index_file}")

    index = read_json(index_file)
    draft_root = select_draft_root(index, draft_root_override)
    base_name = source_draft.name
    target = draft_root / base_name
    if target.exists():
        for number in range(2, 1000):
            target = draft_root / f"{base_name} ({number})"
            if not target.exists():
                break
        else:
            raise RuntimeError("同名草稿过多，无法分配名称")

    # Check every referenced media file before changing the app's draft index.
    content = read_json(source_draft / "draft_content.json")
    sources = {}
    for candidate in source_media.rglob("*"):
        if candidate.is_file():
            if candidate.name in sources:
                raise RuntimeError(f"素材重名，无法安全关联：{candidate.name}")
            sources[candidate.name] = candidate
    media_refs = []
    for group in content.get("materials", {}).values():
        if not isinstance(group, list):
            continue
        for material in group:
            if isinstance(material, dict) and material.get("path"):
                name = PureWindowsPath(material["path"]).name
                if name not in sources:
                    raise RuntimeError(f"工程引用的素材不存在：{name}")
                media_refs.append((material, name))

    shutil.copytree(source_draft, target)
    shutil.copytree(source_media, target / "素材")
    try:
        for material, name in media_refs:
            material["path"] = (target / "素材" / name).as_posix()
        write_json(target / "draft_content.json", content)

        meta = read_json(target / "draft_meta_info.json")
        meta.update(
            draft_name=target.name,
            draft_fold_path=target.as_posix(),
            draft_root_path=target.parent.as_posix(),
            draft_json_file=(target / "draft_content.json").as_posix(),
            draft_id=str(uuid.uuid4()).upper(),
            tm_duration=content.get("duration", 0),
            tm_draft_modified=int(time.time() * 1_000_000),
        )
        write_json(target / "draft_meta_info.json", meta)

        if not isinstance(index.get("all_draft_store"), list):
            raise RuntimeError("剪映草稿索引格式不符合预期")
        index["all_draft_store"].insert(0, copy.deepcopy(meta))
        backup = index_file.with_name(f"root_meta_info.backup_{int(time.time())}.json")
        shutil.copy2(index_file, backup)
        temp_index = index_file.with_name("root_meta_info.installing.json")
        write_json(temp_index, index)
        os.replace(temp_index, index_file)
    except Exception:
        # Leave the copied draft for inspection if registration fails; never delete user files.
        raise
    return target


def main():
    parser = argparse.ArgumentParser(description="把工程与素材安装到剪映本地草稿")
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--index", type=Path, default=Path(os.environ.get("LOCALAPPDATA", "")) / "JianyingPro/User Data/Projects/com.lveditor.draft/root_meta_info.json")
    parser.add_argument("--draft-root")
    args = parser.parse_args()
    try:
        target = install(args.package.resolve(), args.index.resolve(), args.draft_root)
    except Exception as exc:
        print(f"安装失败：{exc}")
        return 1
    print(f"安装成功：{target}")
    print("现在重新打开剪映，在首页「本地草稿」中点击这个工程。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
