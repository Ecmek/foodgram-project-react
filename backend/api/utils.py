from django.db.models.aggregates import Sum
from django.http import HttpResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.decorators import api_view


@api_view(['GET'])
def download_shopping_cart(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="shoppingcart.pdf"'
    p = canvas.Canvas(response)
    x = 50
    y = 800
    indent = 15
    shopping_cart = (
        request.user.shopping_cart.recipe.
        values('ingredients__name', 'ingredients__measurement_unit').
        annotate(amount=Sum('recipe__amount'))
    )
    pdfmetrics.registerFont(
        TTFont('DejaVuSerif', 'DejaVuSerif.ttf', 'UTF-8')
    )
    if not shopping_cart:
        p.setFont('DejaVuSerif', 24)
        p.drawString(x, y, 'Ваш список покупок пуст')
        p.save()
        return response
    p.setFont('DejaVuSerif', 24)
    p.drawString(x, y, 'Ваш список покупок:')
    p.setFont('DejaVuSerif', 16)
    for index, recipe in enumerate(shopping_cart, start=1):
        p.drawString(
            x, y - indent, f'{index}. {recipe["ingredients__name"]} -'
            f'{recipe["amount"]} {recipe["ingredients__measurement_unit"]}.'
        )
        y -= 15
        if y <= 50:
            p.showPage()
            p.setFont('DejaVuSerif', 16)
            y = 800
    p.save()
    return response
