package com.vivero.module.auth.service;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.dto.SocialLoginRequestDto;

public interface AuthService {

    AuthResponseDto login(LoginRequestDto request);

    AuthResponseDto register(RegisterRequestDto request);

    AuthResponseDto refresh(RefreshTokenRequestDto request);

    AuthResponseDto socialLogin(SocialLoginRequestDto request);
}
