/**
 * Safe Fall 로고 컴포넌트
 * - 헤더에 표시되는 브랜드 로고
 * - /Logo.png 이미지 표시
 */
import { useState } from "react";

import "./Logo.css"

function Logo() {
  return (
    <div className="SafeFallLogo">
        <img src="/Logo.png" alt="Logo" />
    </div>
  );
}

export default Logo;
