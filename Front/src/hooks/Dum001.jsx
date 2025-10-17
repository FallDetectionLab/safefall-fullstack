/**
 * 더미 영상 컴포넌트 (Youtube 임베드)
 * - 개발 중 실시간 영상 대체용
 * - 삭제 예정 컴포넌트
 */
import { useState } from "react";

import "./Dum001.css";

function Dum001() {
  return (
    <div>
      <iframe className="dumydata001" src="https://www.youtube.com/embed/Zeiz7nOyPwk?si=GbZ3vbyxjt4kYN2T" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </div>
  );
}

export default Dum001;
