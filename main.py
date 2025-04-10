import os
import shutil
from pathlib import Path
from tqdm import tqdm
import json
import sys

class FileOrganizer:
    def __init__(self):
        self.rule_groups = {
            "默认规则组": {}  # 默认规则组
        }
        self.current_group = "默认规则组"
        self.resources_dir = Path("resources")
        self.resources_dir.mkdir(exist_ok=True)
        self.config_file = self.resources_dir / "file_rules.json"
        self.load_rules()
        self.processed_files = 0
        self.skipped_files = 0
        self.error_files = 0

    def load_rules(self):
        """加载已保存的分类规则"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rule_groups = data.get("rule_groups", {"默认规则组": {}})
                    self.current_group = data.get("current_group", "默认规则组")
            except json.JSONDecodeError:
                print("规则文件损坏，将创建新的规则文件")
                self.rule_groups = {"默认规则组": {}}
                self.current_group = "默认规则组"
        else:
            print("未找到规则文件，将创建新的规则文件")
            self.rule_groups = {"默认规则组": {}}
            self.current_group = "默认规则组"

    def save_rules(self):
        """保存分类规则"""
        try:
            data = {
                "rule_groups": self.rule_groups,
                "current_group": self.current_group
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存规则时出错: {str(e)}")

    def add_rule(self, keyword, folder_name, group_name=None):
        """添加新的分类规则"""
        if not keyword:
            print("关键词不能为空！")
            return False
        
        # 如果文件夹名称为空，则使用关键词作为文件夹名称
        if not folder_name:
            folder_name = keyword
        
        # 规范化文件夹名称
        folder_name = folder_name.strip().replace('/', '_').replace('\\', '_')
        
        # 如果未指定规则组，使用当前规则组
        if group_name is None:
            group_name = self.current_group
        
        # 确保规则组存在
        if group_name not in self.rule_groups:
            self.rule_groups[group_name] = {}
        
        self.rule_groups[group_name][keyword] = folder_name
        self.save_rules()
        return True

    def add_rule_group(self, group_name):
        """添加新的规则组"""
        if not group_name:
            print("规则组名称不能为空！")
            return False
        
        if group_name in self.rule_groups:
            print(f"规则组 '{group_name}' 已存在！")
            return False
        
        self.rule_groups[group_name] = {}
        self.save_rules()
        return True

    def delete_rule_group(self, group_name):
        """删除规则组"""
        if group_name == "默认规则组":
            print("不能删除默认规则组！")
            return False
        
        if group_name not in self.rule_groups:
            print(f"规则组 '{group_name}' 不存在！")
            return False
        
        del self.rule_groups[group_name]
        if self.current_group == group_name:
            self.current_group = "默认规则组"
        self.save_rules()
        return True

    def set_current_group(self, group_name):
        """设置当前规则组"""
        if group_name not in self.rule_groups:
            print(f"规则组 '{group_name}' 不存在！")
            return False
        
        self.current_group = group_name
        self.save_rules()
        return True

    def get_current_rules(self):
        """获取当前规则组的规则"""
        return self.rule_groups.get(self.current_group, {})

    def organize_files(self, source_dir, target_dir, operation_mode='copy'):
        """根据规则整理文件"""
        source_path = Path(source_dir)
        target_path = Path(target_dir)
        
        # 重置计数器
        self.processed_files = 0
        self.skipped_files = 0
        self.error_files = 0

        # 确保目标目录存在
        target_path.mkdir(parents=True, exist_ok=True)

        # 获取当前规则组的规则
        rules = self.get_current_rules()

        # 获取所有文件（包括子目录）
        try:
            files = list(source_path.glob('**/*'))
            total_files = sum(1 for f in files if f.is_file())
            
            if total_files == 0:
                print(f"在 {source_dir} 中没有找到任何文件")
                return
                
            print(f"找到 {total_files} 个文件需要处理")
            print(f"使用规则组: {self.current_group}")
            
            # 使用tqdm显示进度条
            for file_path in tqdm(files, desc="正在整理文件"):
                if file_path.is_file():
                    # 获取文件名和扩展名
                    file_name = file_path.name.lower()
                    file_ext = file_path.suffix.lower()
                    
                    # 跳过隐藏文件
                    if file_name.startswith('.'):
                        self.skipped_files += 1
                        continue
                    
                    # 检查是否匹配任何规则
                    matched = False
                    for keyword, folder_name in rules.items():
                        if keyword.lower() in file_name or keyword.lower() == file_ext:
                            # 创建目标文件夹
                            new_folder = target_path / folder_name
                            new_folder.mkdir(exist_ok=True)

                            # 处理文件（移动或复制）
                            try:
                                # 如果目标文件已存在，添加数字后缀
                                target_file = new_folder / file_path.name
                                if target_file.exists():
                                    base_name = target_file.stem
                                    extension = target_file.suffix
                                    counter = 1
                                    while (new_folder / f"{base_name}_{counter}{extension}").exists():
                                        counter += 1
                                    target_file = new_folder / f"{base_name}_{counter}{extension}"
                                
                                # 根据操作模式选择移动或复制
                                if operation_mode == 'move':
                                    shutil.move(str(file_path), str(target_file))
                                    operation_text = "已移动"
                                else:  # copy
                                    shutil.copy2(str(file_path), str(target_file))
                                    operation_text = "已复制"
                                
                                print(f"{operation_text}: {file_path.name} -> {folder_name}/")
                                self.processed_files += 1
                                matched = True
                                break
                            except Exception as e:
                                print(f"处理文件失败 {file_path.name}: {str(e)}")
                                self.error_files += 1
                    
                    if not matched:
                        self.skipped_files += 1
            
            # 打印统计信息
            print("\n整理完成！统计信息：")
            print(f"成功处理: {self.processed_files} 个文件")
            print(f"跳过: {self.skipped_files} 个文件")
            print(f"处理失败: {self.error_files} 个文件")
            
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")

def get_valid_path(prompt, must_exist=False):
    """获取有效的路径输入"""
    while True:
        path = input(prompt).strip()
        if not path:
            print("路径不能为空！")
            continue
            
        # 展开用户目录的波浪号
        if path.startswith('~'):
            path = os.path.expanduser(path)
            
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            print(f"路径 '{path}' 不存在！")
            continue
            
        return str(path_obj)

def get_operation_mode():
    """获取用户选择的操作模式"""
    while True:
        print("\n请选择操作模式：")
        print("1. 复制文件（保留源目录中的文件，同时复制到目标目录）")
        print("2. 移动文件（将文件从源目录移动到目标目录）")
        
        choice = input("请选择 (1-2): ").strip()
        
        if choice == "1":
            return "copy"
        elif choice == "2":
            return "move"
        else:
            print("无效的选择，请重试！")

def main():
    # 确保resources目录存在
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    organizer = FileOrganizer()
    
    while True:
        print("\n=== 文件整理助手 ===")
        print("1. 添加分类规则")
        print("2. 开始整理文件")
        print("3. 查看当前规则")
        print("4. 删除规则")
        print("5. 规则组管理")
        print("6. 关于")
        print("7. 退出")
        
        try:
            choice = input("\n请选择操作 (1-7): ")
            
            if choice == "1":
                keyword = input("请输入关键词或文件扩展名（如 .pdf）: ")
                folder_name = input("请输入对应的文件夹名称（留空则使用关键词）: ")
                group_name = input("请输入规则组名称（留空则使用当前规则组）: ")
                if organizer.add_rule(keyword, folder_name, group_name):
                    print(f"已添加规则: {keyword} -> {folder_name or keyword}")
                
            elif choice == "2":
                source_dir = get_valid_path("请输入要整理的文件夹路径: ", must_exist=True)
                target_dir = get_valid_path("请输入整理后的文件存放路径: ")
                
                # 检查源目录和目标目录是否相同
                if os.path.abspath(source_dir) == os.path.abspath(target_dir):
                    print("源目录和目标目录不能相同！")
                    continue
                
                # 获取用户选择的操作模式
                operation_mode = get_operation_mode()
                
                organizer.organize_files(source_dir, target_dir, operation_mode)
                
            elif choice == "3":
                current_rules = organizer.get_current_rules()
                if not current_rules:
                    print("\n当前规则组没有分类规则")
                else:
                    print(f"\n当前规则组 '{organizer.current_group}' 的分类规则：")
                    for keyword, folder in current_rules.items():
                        print(f"{keyword} -> {folder}")
                
            elif choice == "4":
                current_rules = organizer.get_current_rules()
                if not current_rules:
                    print("\n当前规则组没有分类规则")
                    continue
                    
                print(f"\n当前规则组 '{organizer.current_group}' 的分类规则：")
                for i, (keyword, folder) in enumerate(current_rules.items(), 1):
                    print(f"{i}. {keyword} -> {folder}")
                
                try:
                    rule_index = int(input("\n请输入要删除的规则编号 (0 取消): "))
                    if rule_index == 0:
                        continue
                        
                    if 1 <= rule_index <= len(current_rules):
                        keyword = list(current_rules.keys())[rule_index - 1]
                        del organizer.rule_groups[organizer.current_group][keyword]
                        organizer.save_rules()
                        print(f"已删除规则: {keyword}")
                    else:
                        print("无效的规则编号！")
                except ValueError:
                    print("请输入有效的数字！")
                
            elif choice == "5":
                while True:
                    print("\n=== 规则组管理 ===")
                    print("1. 查看所有规则组")
                    print("2. 添加规则组")
                    print("3. 删除规则组")
                    print("4. 切换当前规则组")
                    print("5. 返回主菜单")
                    
                    sub_choice = input("\n请选择操作 (1-5): ")
                    
                    if sub_choice == "1":
                        print("\n所有规则组：")
                        for i, group_name in enumerate(organizer.rule_groups.keys(), 1):
                            prefix = "* " if group_name == organizer.current_group else "  "
                            print(f"{prefix}{i}. {group_name}")
                            rules = organizer.rule_groups[group_name]
                            if rules:
                                print("   规则：")
                                for keyword, folder in rules.items():
                                    print(f"   - {keyword} -> {folder}")
                            else:
                                print("   暂无规则")
                    
                    elif sub_choice == "2":
                        group_name = input("请输入新规则组名称: ")
                        if organizer.add_rule_group(group_name):
                            print(f"已添加规则组: {group_name}")
                    
                    elif sub_choice == "3":
                        if len(organizer.rule_groups) <= 1:
                            print("至少保留一个规则组！")
                            continue
                            
                        print("\n可删除的规则组：")
                        for i, group_name in enumerate(organizer.rule_groups.keys(), 1):
                            if group_name != "默认规则组":
                                print(f"{i}. {group_name}")
                        
                        try:
                            group_index = int(input("\n请输入要删除的规则组编号 (0 取消): "))
                            if group_index == 0:
                                continue
                                
                            group_names = [name for name in organizer.rule_groups.keys() if name != "默认规则组"]
                            if 1 <= group_index <= len(group_names):
                                group_name = group_names[group_index - 1]
                                if organizer.delete_rule_group(group_name):
                                    print(f"已删除规则组: {group_name}")
                            else:
                                print("无效的规则组编号！")
                        except ValueError:
                            print("请输入有效的数字！")
                    
                    elif sub_choice == "4":
                        print("\n可切换的规则组：")
                        for i, group_name in enumerate(organizer.rule_groups.keys(), 1):
                            prefix = "* " if group_name == organizer.current_group else "  "
                            print(f"{prefix}{i}. {group_name}")
                        
                        try:
                            group_index = int(input("\n请输入要切换的规则组编号 (0 取消): "))
                            if group_index == 0:
                                continue
                                
                            if 1 <= group_index <= len(organizer.rule_groups):
                                group_name = list(organizer.rule_groups.keys())[group_index - 1]
                                if organizer.set_current_group(group_name):
                                    print(f"已切换到规则组: {group_name}")
                            else:
                                print("无效的规则组编号！")
                        except ValueError:
                            print("请输入有效的数字！")
                    
                    elif sub_choice == "5":
                        break
                    
                    else:
                        print("无效的选择，请重试！")
                
            elif choice == "6":
                print("\n=== 关于 ===")
                print("文件整理助手 v1.4.0")
                print("一个固定规则的文件分类工具，可以根据文件名中的关键词或文件类型自动将文件分类到不同的文件夹中。")
                print("\n开发者信息：")
                print("开发者: cxin")
                print("邮箱: tojx@qq.com")
                print("个人网站: www.cxin.net")
                print("\n© 2023 cxin. 保留所有权利。")
                input("\n按回车键继续...")
                
            elif choice == "7":
                print("感谢使用！再见！")
                break
                
            else:
                print("无效的选择，请重试！")
                
        except KeyboardInterrupt:
            print("\n操作已取消")
        except Exception as e:
            print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"程序发生错误: {str(e)}")
        input("按回车键退出...") 