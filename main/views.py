from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Category, Product, Size
from django.db.models import Q
#нам нужно настроить на то, чтобы они возращали не шаблон, а они будут возвращать блок контента, который мы
#вставляем в base.html и этот блок имеет внутри свой backend


class IndexView(TemplateView):
    template_name = 'main/base.html' #наша база, где у нас есть блок contenta, который мы будем менять
    
    def get_context_data(self, **kwargs):
        context = super.get_context_data(**kwargs)
        context['categories'] = Category.objects.all() # выводим все категории, которые у нас есть в бд
        context['current_category'] = None
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)
    
    
class CatalogView(TemplateView):
    template = 'main/base.html'
    
    #флажки, сразу выполниться по данным параметрам
    FILTER_MAPPING = {
        'color': lambda queryset, value: queryset.filter(color__iexact = value),
        'min_price': lambda queryset, value: queryset.filter(price_gte = value),
        'max_price': lambda queryset, value: queryset.filter(price_lte = value),
        'size': lambda queryset, value: queryset.filter(product_size__size__name = value),
    }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.all()
        products = Product.objects.all().order_by('-created_at')
        current_category = None
        
        if category_slug:
            current_category = get_object_or_404(Category, slug = category_slug)#пытаемся достать категорию по тому слагу который он указал 
            products = products.filter(category = current_category)#filter - сортировка
            
        query = self.request.GET.get('q')# q = ... человек пишет
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query) #пытаемся найти в названии в дескрипшион
            )
            
        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)
            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ' '
                
        filter_params['q'] = query or ' '
        
        context.update({
            'categories' : categories,
            'products' : products,
            'current_category' : category_slug,
            'filter_params' : filter_params,
            'sizes' : Size.object.all(),
            'search_query' : query or ' '
        })
        
        if self.request.GET.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.GET.get('reset_search') == 'true':
            context['reset_search'] = True
        return
    
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            template = 'main/filter_modal.html' if request.GET.get('show_filters') == 'true' else 'main/catalog.html'#модалка где все параметры для фильтрации каталога
            return TemplateResponse(request, template, context)
        return TemplateResponse(request, self.template_name, context)
    
    
    
class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):#self - тело запроса
        context = super().get_context_data(**kwargs)
        product = self.get_object()# достаем продукт
        context['categories'] = Category.objects.all()#после чего показываем его
        context['related_products'] = Product.objects.filter(
            category = product.category
        ).exclude(id = product.id)[:4]
        context['current_category'] = product.category.slug
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        raise TemplateResponse(request, self.template_name, context)