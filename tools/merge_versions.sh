#!/bin/bash

input_dir="."
output_dir="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)
      input_dir="$2"
      shift 2
      ;;
    -o|--output)
      output_dir="$2"
      shift 2
      ;;
    -h|--help)
      echo "用法: $0 [-i 输入目录] [-o 输出目录]"
      echo "  -i, --input   输入目录（默认: 当前目录）"
      echo "  -o, --output  输出目录（默认: 当前目录）"
      exit 0
      ;;
    *)
      echo "未知参数: $1"
      echo "使用 -h 查看帮助"
      exit 1
      ;;
  esac
done

if [ ! -d "$input_dir" ]; then
  echo "错误: 输入目录不存在: $input_dir"
  exit 1
fi

mkdir -p "$output_dir"

versions=$(find "$input_dir" -maxdepth 1 -type f -name '[0-9]*.[0-9]*' | \
  grep -oE '[0-9]+\.[0-9]+' | sort -V -u)

if [ -z "$versions" ]; then
  echo "在 $input_dir 中未找到版本号格式的文件"
  exit 1
fi

count=0
for version in $versions; do
  shopt -s nullglob
  files=("$input_dir"/${version}*)
  shopt -u nullglob
  
  if [ ${#files[@]} -gt 0 ]; then
    sorted_files=()
    while IFS= read -r line; do
        sorted_files+=("$line")
    done < <(printf '%s\n' "${files[@]}" | sort -V)
    cat "${sorted_files[@]}" > "$output_dir/${version}_merged.md"
    echo "已合并: ${version}_merged.md (${#files[@]} 个文件)"
    count=$((count + 1))
  fi
done

echo "完成！共合并 $count 个版本，文件保存在: $output_dir"
