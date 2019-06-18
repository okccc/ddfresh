from django.db import models


class BaseModel(models.Model):
    """模型抽象基类"""
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    isDelete = models.BooleanField(default=False, verbose_name="删除标记")

    class Meta:
        # 这是一个抽象模型类
        abstract = True
