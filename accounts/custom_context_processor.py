


def custom_user_context(request):
    if request.user.is_authenticated:
        user = request.user
        return {
            'user': user,
        }
    return {}