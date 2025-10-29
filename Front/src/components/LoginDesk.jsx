/**
 * 데스크톱 버전 로그인 버튼 컴포넌트
 * - 로그인 상태에 따라 다른 UI 표시
 * - 로그인 전: Sign In, Sign Up, 문의하기
 * - 로그인 후: Log out, 사용자 ID
 */
import { useState } from "react";

import "./LoginDesk.css";

function LoginDesk({ isLoggedIn, currentUser, onLogin, onSignup, onLogout }) {
  
  if (isLoggedIn && currentUser) {
    // 로그인된 상태 UI
    return (
      <div className="SignInSignUpContactUsBtn">
        <button onClick={onLogout}>Log out</button>
        <p
          onClick={onLogout}
          style={{ cursor: 'pointer', color: '#69BDF9' }}
          className="user-id-text"
        >
          {currentUser.username || currentUser.id}
        </p>
      </div>
    );
  }

  // 로그인 안된 상태 UI (기존)
  return (
    <div className="SignInSignUpContactUsBtn">
      <button>문의하기</button>
      <p>/</p>
      <button onClick={onLogin}>Sign In</button>
      <p>/</p>
      <button onClick={onSignup}>Sign Up</button>
    </div>
  );
}

export default LoginDesk;