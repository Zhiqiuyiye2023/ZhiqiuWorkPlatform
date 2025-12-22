"""
文件处理功能管理器
作者: 知秋一叶
版本号: 0.0.5
"""

from PyQt6.QtWidgets import QMessageBox


class FileFunctionManager:
    """文件处理功能管理器"""
    
    @staticmethod
    def openFunction(func_id: str, parent=None):
        """打开文件处理功能"""
        try:
            if func_id == "file_stat":
                # 打开文件统计功能
                from functions.stat_dialog import FileStatDialog
                dialog = FileStatDialog(parent)
                dialog.exec()
            elif func_id == "move_copy":
                # 打开移动复制功能
                from functions.move_copy_dialog import MoveCopyDialog
                dialog = MoveCopyDialog(parent)
                dialog.exec()
            elif func_id == "data_process":
                # 打开数据处理功能
                from functions.data_process_dialog import DataProcessDialog
                dialog = DataProcessDialog(parent)
                dialog.exec()
            elif func_id == "batch_rename":
                # 打开批量重命名功能
                from functions.rename_dialog import RenameDialog
                dialog = RenameDialog(parent)
                dialog.exec()
            elif func_id == "batch_copy_move":
                # 打开批量操作功能
                from functions.batch_copy_move_dialog import BatchCopyMoveDialog
                dialog = BatchCopyMoveDialog(parent)
                dialog.exec()
            elif func_id == "file_table_compare":
                # 打开表格比对功能
                from functions.table_compare_dialog import TableCompareDialog
                dialog = TableCompareDialog(parent)
                dialog.exec()
            else:
                # 未知功能
                QMessageBox.warning(parent, "警告", f"未知的功能ID: {func_id}")
        except Exception as e:
            QMessageBox.critical(parent, "错误", f"打开功能时出错: {str(e)}")