from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import logout
from .forms import DeleteAccountForm
from django.shortcuts import redirect


@login_required
def delete_account(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            logout(request)
            user.delete()
            messages.success(request,
                             _("Your account has been successfully deleted."))
            return redirect('home')
    else:
        form = DeleteAccountForm(request.user)

    return render(request, 'account/delete_account.html', {'form': form})
