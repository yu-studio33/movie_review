from django import forms
from django.contrib.auth.models import User
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'この映画の感想を書いてください'}),
        }
        labels = {
            'rating': '評価',
            'comment': 'コメント',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].initial = 5


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].max_length = 20
        self.fields['username'].help_text = '半角英数字で入力してください（20文字以内）'
