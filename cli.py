#!/usr/bin/env python3
"""
PDF翻译工具命令行入口

Usage:
    pdftrans translate <input> [options]
    pdftrans glossary <input> [options]
    pdftrans list-languages
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.translate_command import translate_handler
from cli.glossary_command import glossary_handler
from cli.list_languages_command import list_languages_handler


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """自定义帮助信息格式化器，在主帮助中显示子命令的详细参数"""
    
    def _format_action(self, action):
        """格式化动作，为子命令添加详细参数"""
        # 处理子命令动作
        if action.nargs == argparse.PARSER:
            # 为每个子命令添加详细参数
            if action.choices:
                subcommand_details = []
                subcommand_details.append('')
                subcommand_details.append('子命令详情:')
                subcommand_details.append('')
                
                for command_name, command_parser in action.choices.items():
                    subcommand_details.append(f'  {command_name}')
                    if command_parser.description:
                        subcommand_details.append(f'    {command_parser.description}')
                    
                    # 添加子命令的参数
                    if command_parser._actions:
                        subcommand_details.append('')
                        subcommand_details.append('    参数:')
                        subcommand_details.append('')
                        
                        # 过滤掉help参数
                        for sub_action in command_parser._actions:
                            if sub_action.dest == 'help':
                                continue
                            
                            # 生成参数行
                            if sub_action.option_strings:
                                # 选项参数
                                opt_str = ', '.join(sub_action.option_strings)
                                if sub_action.default is not argparse.SUPPRESS:
                                    if isinstance(sub_action.default, bool):
                                        if sub_action.default:
                                            default_str = ' (默认: True)'
                                        else:
                                            default_str = ''
                                    elif sub_action.default is None:
                                        default_str = ' (默认: 自动生成)'
                                    else:
                                        default_str = f' (默认: {sub_action.default})'
                                else:
                                    default_str = ''
                                subcommand_details.append(f'      {opt_str}{default_str}')
                                if sub_action.help:
                                    subcommand_details.append(f'          {sub_action.help}')
                            else:
                                # 位置参数
                                if sub_action.help:
                                    subcommand_details.append(f'      {sub_action.dest}')
                                    subcommand_details.append(f'          {sub_action.help}')
                        subcommand_details.append('')
                
                # 调用父类方法获取基本格式
                parts = super()._format_action(action)
                # 将子命令详细信息添加到原始格式中
                parts = parts.rstrip() + '\n' + '\n'.join(subcommand_details)
                return parts
        
        # 处理其他动作
        return super()._format_action(action)


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='pdftrans',
        description='PDF翻译工具 - 支持多翻译API的PDF翻译命令行工具',
        formatter_class=CustomHelpFormatter,
        epilog="""
使用示例:
  %(prog)s translate document.pdf -o translated.pdf
  %(prog)s translate document.pdf -s en -t zh -T silicon_flow
  %(prog)s translate document.pdf --pages "1-10,15" -f docx
  %(prog)s glossary document.pdf -o glossary.txt
  %(prog)s list-languages
        """
    )
    
    # 全局选项
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细输出'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # translate 子命令
    translate_parser = subparsers.add_parser(
        'translate',
        help='翻译PDF文件',
        description='翻译PDF文件为目标语言'
    )
    translate_parser.add_argument(
        'input',
        help='输入PDF文件路径'
    )
    translate_parser.add_argument(
        '-o', '--output',
        help='输出文件路径（默认：自动生成）'
    )
    translate_parser.add_argument(
        '-s', '--source',
        default='en',
        choices=['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru'],
        help='源语言代码（默认：en）'
    )
    translate_parser.add_argument(
        '-t', '--target',
        default='zh',
        choices=['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru'],
        help='目标语言代码（默认：zh）'
    )
    translate_parser.add_argument(
        '-T', '--translator',
        default='aiping',
        choices=['aiping', 'silicon_flow'],
        help='翻译服务类型（默认：aiping）'
    )
    translate_parser.add_argument(
        '-p', '--pages',
        help='页码范围，如"1-5,7,9-10"'
    )
    translate_parser.add_argument(
        '-f', '--format',
        default='pdf',
        choices=['pdf', 'docx', 'markdown'],
        help='输出格式（默认：pdf）'
    )
    translate_parser.add_argument(
        '-g', '--glossary',
        help='术语表文件路径'
    )
    translate_parser.add_argument(
        '-d', '--doc-type',
        default='AI技术',
        help='文档类型或领域说明（默认：AI技术）'
    )
    translate_parser.add_argument(
        '-m', '--semantic-merge',
        action='store_true',
        help='启用语义合并'
    )
    translate_parser.add_argument(
        '-l', '--llm-merge',
        action='store_true',
        help='使用LLM合并'
    )
    translate_parser.add_argument(
        '-c', '--chapter-split',
        action='store_true',
        help='按章节拆分输出Markdown（只在选择Markdown输出格式时起作用）'
    )
    
    # glossary 子命令
    glossary_parser = subparsers.add_parser(
        'glossary',
        help='提取术语表',
        description='从PDF文件中提取术语表'
    )
    glossary_parser.add_argument(
        'input',
        help='输入PDF文件路径'
    )
    glossary_parser.add_argument(
        '-o', '--output',
        help='输出文件路径（默认：自动生成）'
    )
    glossary_parser.add_argument(
        '-s', '--source',
        default='en',
        choices=['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru'],
        help='源语言代码（默认：en）'
    )
    glossary_parser.add_argument(
        '-t', '--target',
        default='zh',
        choices=['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru'],
        help='目标语言代码（默认：zh）'
    )
    glossary_parser.add_argument(
        '-T', '--translator',
        default='aiping',
        choices=['aiping', 'silicon_flow'],
        help='翻译服务类型（默认：aiping）'
    )
    glossary_parser.add_argument(
        '-p', '--pages',
        help='页码范围，如"1-5,7,9-10"'
    )
    glossary_parser.add_argument(
        '-d', '--doc-type',
        default='AI技术',
        help='文档类型或领域说明（默认：AI技术）'
    )
    
    # list-languages 子命令
    subparsers.add_parser(
        'list-languages',
        help='列出支持的语言',
        description='显示所有支持的语言代码和名称'
    )
    
    return parser


def main():
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 路由到对应的处理函数
    try:
        if args.command == 'translate':
            translate_handler(args)
        elif args.command == 'glossary':
            glossary_handler(args)
        elif args.command == 'list-languages':
            list_languages_handler(args)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
