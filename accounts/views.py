from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import logout
from .forms import DeleteAccountForm
from django.shortcuts import redirect
from allauth.account.views import SignupView
from .forms import CustomSignupForm


class CustomSignupView(SignupView):
    form_class = CustomSignupForm

    def get_initial(self):
        initial = super().get_initial()

        # Get email from query parameter if it exists
        email = self.request.GET.get('email', '')
        if email:
            initial['email'] = email

        # Check if newsletter interest was indicated
        if self.request.GET.get('newsletter_interest'):
            initial['newsletter_opt_in'] = True

        return initial


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
