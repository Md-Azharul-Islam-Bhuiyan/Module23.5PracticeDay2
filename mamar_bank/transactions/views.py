from django.urls import reverse_lazy
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .forms import DepositeForm, WithdrawForm, LoanRequestForm, TransferBalanceForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, View, FormView
from django.views import View as viw
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from transactions.models import Transaction
from .constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID, BALANCE_TRANSFER
from datetime import datetime
from django.db.models import Sum
from accounts.models import UserBankAccount

def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template,{
        'user': user, 
        'amount': amount
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, "text/html")
    send_email.send()


class TransactinViewsMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })
        
        return context
    

class DepositMoneyView(TransactinViewsMixin):
    form_class = DepositeForm
    title = 'Deposite Form'

    def get_initial(self):
         initial = {'transaction_type': DEPOSIT}
         return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount

        account.save(
           update_fields= [
               'balance'
            ]
        )

        messages.success(self.request, f'{"{:,.2f}".format(float(amount))}৳ was deposited to your account successfully')

        send_transaction_email(self.request.user, amount, "Deposite Messages", 'transactions/deposite_email.html')
        return super().form_valid(form)


class WithdrawMoneyView(TransactinViewsMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
         initial = {'transaction_type': WITHDRAWAL}
         return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        if account.is_bancrupt:
            messages.error(self.request, 'Bancurpt!! You cannot withdraw your deposite money')
            return redirect('home')

        account.balance -= amount

        account.save(
           update_fields= [
               'balance'
            ]
        )

        messages.success(self.request, f'You successfully withdraw {"{:,.2f}".format(float(amount))}৳ from your account')

        send_transaction_email(self.request.user, amount, "Withdrawal Messages", 'transactions/withdrawal_email.html')
        return super().form_valid(form)


class LoanRequestView(TransactinViewsMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'



    def get_initial(self):
         initial = {'transaction_type': LOAN}
         return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        
        current_loan_count = Transaction.objects.filter(account= self.request.user.account, transaction_type = 3, approve = True).count()

        if current_loan_count >= 3:
            return HttpResponse('You have crossed your limits')

        messages.success(self.request, f'Loan request for {"{:,.2f}".format(float(amount))}৳ has been successfully sent to admin')
        send_transaction_email(self.request.user, amount, "Loan Request Messages", 'transactions/loan_email.html')
        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin , ListView): 
    template_name='transactions/transaction_report.html'
    model = Transaction
    balance = 0

    def get_queryset(self) :
        queryset= super().get_queryset().filter(
            account = self.request.user.account
        )
    
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() 
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(timestamp__date__gte= start_date, timestamp__date__lte= end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance


        return queryset.distinct() 
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
        
        return context


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request,loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)

        if loan.approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balanace_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            
            else:
                messages.error(self.request, f'Loan amount is greater than available balance')
                return redirect('loan_list')
            
class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account, transaction_type=LOAN)
        return queryset


class TransferBalanceView(LoginRequiredMixin,FormView):
    form_class = TransferBalanceForm
    template_name = 'transactions/transfer_balance.html'
    
    
    def get_initial(self):
         initial = {'transaction_type': BALANCE_TRANSFER}
         return initial

    def form_valid(self, form):
        sender = self.request.user.account
      
        recevier_acc_no = form.cleaned_data.get('account')
        transfer_amount = form.cleaned_data.get('amount')
        
        try:
            recevier_acc = UserBankAccount.objects.get(account_no=recevier_acc_no)

            # print(recevier_acc)
            if sender.balance >=0 and transfer_amount<=sender.balance:
                recevier_acc.balance += transfer_amount
                sender.balance -= transfer_amount
                recevier_acc.save()
                sender.save()
                

                Transaction.objects.create(
                    account=sender,
                    amount=transfer_amount,
                    balanace_after_transaction=sender.balance,
                    transaction_type=BALANCE_TRANSFER,
                    approve=True 
                )

                messages.success(self.request, f'You have Transfered {"{:,.2f}".format(float(transfer_amount))}৳ Successfully.')
                send_transaction_email(self.request.user, transfer_amount, "Balance Transfer Messages", 'transactions/transfer_email.html')   
                send_transaction_email(recevier_acc.user, transfer_amount, "Balance Receive Messages", 'transactions/receive_email.html')   
                return redirect('balance_transfer')
            else:
                messages.error(self.request, 'Your Balance Insuffient')
                return redirect('balance_transfer')
        except UserBankAccount.DoesNotExist:
            messages.error(self.request, 'Your given acc no does not exist')

            
        return super().form_valid(form)
    

