# -*- coding: utf-8 -*-
"""数据模型可复制功能 Mixin"""

import copy as copy_module


class CopyableMixin:
    """提供 copy 功能的 Mixin 类
    
    继承该类的数据模型将自动获得 copy() 和 deepcopy() 方法
    """
    
    def copy(self, exclude_attrs=None):
        """创建对象的浅拷贝
        
        Args:
            exclude_attrs (list): 要排除的属性名列表，默认不排除任何属性
            
        Returns:
            新的对象实例
        """
        exclude_attrs = exclude_attrs or []
        
        new_obj = copy_module.copy(self)
        
        for attr in exclude_attrs:
            setattr(new_obj, attr, None)
        
        return new_obj
    
    def deepcopy(self, exclude_attrs=None):
        """创建对象的深拷贝
        
        Args:
            exclude_attrs (list): 要排除的属性名列表，默认不排除任何属性
            
        Returns:
            新的对象实例
        """
        exclude_attrs = exclude_attrs or []
        
        new_obj = copy_module.deepcopy(self)
        
        for attr in exclude_attrs:
            setattr(new_obj, attr, None)
        
        return new_obj
