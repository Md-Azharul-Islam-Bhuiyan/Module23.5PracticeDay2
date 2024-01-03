from django import forms
from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']
    
    def __init__(self, *args, **kwargs):
        self.user_account = kwargs.pop('account') # account value ke pop kore anlam
        super().__init__( *args, **kwargs)
        self.fields['transaction_type'].disabled = True # ei field disable thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput() # user er theke hide kora thakbe
    
    def save(self, commit=True):
        self.instance.account = self.user_account
        self.instance.balanace_after_transaction = self.user_account.balance
        return super().save()

class DepositeForm(TransactionForm):
    def clean_amount(self):
        min_deposite_amount = 500
        amount = self.cleaned_data.get('amount')
        if amount < min_deposite_amount:
            raise forms.ValidationError(
                f'You need to deposite at least {min_deposite_amount}Tk.'
            )
        return amount
    

class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.user_account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount}'
            )
        
        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount}'
            )
        
        if amount > balance :
            raise forms.ValidationError(
                f'You have {balance}Tk. in your account.\nYou can not withdraw more than your account balance'
            )
        return amount


class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount

class TransferBalanceForm(forms.Form):
    account = forms.IntegerField()
    amount = forms.IntegerField()
    
    
