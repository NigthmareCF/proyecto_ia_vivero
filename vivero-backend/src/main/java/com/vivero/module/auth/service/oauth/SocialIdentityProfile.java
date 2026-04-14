package com.vivero.module.auth.service.oauth;

import com.vivero.shared.enums.AuthProvider;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class SocialIdentityProfile {
    AuthProvider provider;
    String providerUserId;
    String email;
    boolean emailVerified;
    String firstName;
    String lastName;
    String fullName;
    String avatarUrl;
}
