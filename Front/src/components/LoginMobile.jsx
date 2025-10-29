/**
 * 모바일 버전 햄버거 메뉴 아이콘 컴포넌트
 * - 3줄 햄버거 메뉴 SVG 아이콘
 * - 클릭 시 TMslideMenu 열림
 */
import { useState } from "react";

import "./LoginMobile.css";

function LoginMobile() {
  return (
    <div>
      <svg
        width="20"
        height="16"
        viewBox="0 0 20 16"
        fill="none"
      >
        <g>
          <rect width="20" height="2" fill="#222222" />
          <rect y="7" width="20" height="2" fill="#222222" />
          <rect y="14" width="20" height="2" fill="#222222" />
        </g>
        <defs>
            <rect width="20" height="16" rx="1" fill="white" />
        </defs>
      </svg>
    </div>
  );
}

export default LoginMobile;
