class UserProcessor:
    def segregate_users(self, valid_users):
        retail_users = []
        corporate_users = []

        for user in valid_users:
            is_corp_user = user.get("_is_corp_user_normalized")

            if is_corp_user is True:
                corporate_users.append(user)
            else:
                retail_users.append(user)

        return {
            "retail_users": retail_users,
            "corporate_users": corporate_users,
            "total_retail_users": len(retail_users),
            "total_corporate_users": len(corporate_users)
        }