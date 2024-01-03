from django.contrib import admin
from accounts.models import UserBankAccount,UserAddress

admin.site.register(UserBankAccount)
admin.site.register(UserAddress)
