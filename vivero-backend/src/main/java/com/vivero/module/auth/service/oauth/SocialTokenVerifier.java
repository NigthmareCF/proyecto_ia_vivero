package com.vivero.module.auth.service.oauth;

import com.vivero.shared.enums.AuthProvider;

public interface SocialTokenVerifier {

    SocialIdentityProfile verify(AuthProvider provider, String idToken);
}
