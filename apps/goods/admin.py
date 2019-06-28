from django.contrib import admin
from django.core.cache import cache
from apps.goods.models import GoodsType, IndexPromotionBanner, IndexGoodsBanner, IndexTypeGoodsBanner
from celery_tasks.tasks import generate_static_index_html  # 通过celery生成首页静态页面
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """新增/更新表中数据时调用"""
        super().save_model(request, obj, form, change)
        # 发出任务,让celery worker重新生成首页静态页
        generate_static_index_html.delay()
        # 修改数据后清除首页的缓存数据
        cache.delete(key='index_page_data')

    def delete_model(self, request, obj):
        """删除表中数据时调用"""
        super().delete_model(request, obj)
        # 发出任务,让celery worker重新生成首页静态页
        generate_static_index_html.delay()
        # 删除数据后清除首页的缓存数据
        cache.delete(key='index_page_data')


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


# 注册模型类到admin站点
admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
