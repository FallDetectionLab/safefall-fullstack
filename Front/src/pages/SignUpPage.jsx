/**
 * 회원가입 페이지 컴포넌트
 * - 사용자 회원가입 처리 (아이디, 닉네임, 비밀번호, 이메일)
 * - 유효성 검사 (ID, Username, Password 등)
 * - 회원가입 성공 시 자동 로그인 후 대시보드로 이동
 * - 비밀번호 표시/숨김 토글 기능
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import httpClient from "../services/httpClient";

import "./SignUpPage.css";

function SignUpPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    id: "",
    username: "",
    password: "",
    confirmPassword: "",
    email: "",
  });

  const [errors, setErrors] = useState({
    id: "",
    username: "",
    password: "",
    confirmPassword: "",
    email: "",
    general: "",
  });

  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // 입력값 변경 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // 입력 시 해당 필드의 에러 메시지 제거
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
        general: "",
      }));
    }
  };

  // 유효성 검사 함수
  const validateForm = () => {
    const newErrors = {
      id: "",
      username: "",
      password: "",
      confirmPassword: "",
      email: "",
      general: "",
    };

    let isValid = true;

    // ID 검증 (필수, 3-50자)
    if (!formData.id.trim()) {
      newErrors.id = "아이디를 입력해주세요.";
      isValid = false;
    } else if (formData.id.length < 3 || formData.id.length > 50) {
      newErrors.id = "아이디는 3자 이상 50자 이하로 입력해주세요.";
      isValid = false;
    }

    // Username 검증 (필수, 2-50자)
    if (!formData.username.trim()) {
      newErrors.username = "닉네임을 입력해주세요.";
      isValid = false;
    } else if (formData.username.length < 2 || formData.username.length > 50) {
      newErrors.username = "닉네임은 2자 이상 50자 이하로 입력해주세요.";
      isValid = false;
    }

    // Password 검증 (필수, 8자 이상)
    if (!formData.password) {
      newErrors.password = "비밀번호를 입력해주세요.";
      isValid = false;
    } else if (formData.password.length < 8) {
      newErrors.password = "비밀번호는 8자 이상이어야 합니다.";
      isValid = false;
    }

    // Confirm Password 검증 (비밀번호 일치)
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호 확인을 입력해주세요.";
      isValid = false;
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호가 일치하지 않습니다.";
      isValid = false;
    }

    // Email 검증 (선택 사항, 입력 시 이메일 형식 검증)
    if (formData.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        newErrors.email = "올바른 이메일 형식이 아닙니다.";
        isValid = false;
      }
    }

    setErrors(newErrors);
    return isValid;
  };

  // 회원가입 제출 핸들러
  const handleSubmit = async (e) => {
    e.preventDefault();

    // 유효성 검사
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors((prev) => ({ ...prev, general: "" }));

    try {
      // 회원가입 API 호출
      const registerPayload = {
        id: formData.id.trim(),
        username: formData.username.trim(),
        password: formData.password,
        email: formData.email.trim() || undefined, // 빈 문자열인 경우 undefined로 전송
      };

      const registerResponse = await httpClient.post('/api/auth/register', registerPayload);

      // 회원가입 성공 시 자동 로그인 처리
      if (registerResponse.success || registerResponse.message === "User registered successfully") {
        try {
          // 로그인 API 호출
          const loginResponse = await httpClient.post('/api/auth/login', {
            id: formData.id.trim(),  // username → id로 수정
            password: formData.password,
          });

          // JWT 토큰 저장
          if (loginResponse && loginResponse.access_token) {
            localStorage.setItem('access_token', loginResponse.access_token);
            if (loginResponse.refresh_token) {
              localStorage.setItem('refresh_token', loginResponse.refresh_token);
            }

            // httpClient에 토큰 설정
            httpClient.setAuthToken(loginResponse.access_token);
            if (loginResponse.refresh_token) {
              httpClient.setRefreshToken(loginResponse.refresh_token);
            }
          }

          // 사용자 정보로 로그인 처리
          const user = loginResponse?.user || {
            id: formData.id.trim(),
            username: formData.username.trim(),
            name: formData.username.trim(),
          };

          login(user);

          // 대시보드로 리다이렉트
          navigate('/dashboard');
        } catch (loginError) {

          // 자동 로그인 실패 시 로그인 페이지로 이동
          setErrors((prev) => ({
            ...prev,
            general: "회원가입은 완료되었으나 자동 로그인에 실패했습니다. 로그인 페이지로 이동합니다.",
          }));

          setTimeout(() => {
            navigate('/login');
          }, 2000);
        }
      } else {
        setErrors((prev) => ({
          ...prev,
          general: "회원가입에 실패했습니다. 다시 시도해주세요.",
        }));
      }
    } catch (error) {

      // 에러 메시지 처리
      let errorMessage = "회원가입 중 오류가 발생했습니다.";

      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        if (status === 409) {
          // 중복 ID/이메일
          errorMessage = data.message || "이미 존재하는 아이디 또는 이메일입니다.";
        } else if (status === 400) {
          // 잘못된 요청
          errorMessage = data.message || "입력한 정보를 확인해주세요.";
        } else if (status === 500) {
          // 서버 에러
          errorMessage = "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
        }
      } else if (error.request) {
        // 네트워크 에러
        errorMessage = "서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.";
      }

      setErrors((prev) => ({
        ...prev,
        general: errorMessage,
      }));
    } finally {
      setIsLoading(false);
    }
  };

  // 취소 버튼 핸들러
  const handleCancel = () => {
    navigate('/login');
  };

  return (
    <div className="signup-page">
      <div className="signup-container">
        <h1>SafeFall 회원가입</h1>

        <form onSubmit={handleSubmit} className="signup-form">
          {/* 아이디 입력 */}
          <div className="form-group">
            <label htmlFor="id">
              아이디 <span className="required">*</span>
            </label>
            <input
              type="text"
              id="id"
              name="id"
              value={formData.id}
              onChange={handleInputChange}
              placeholder="로그인에 사용할 아이디 (3-50자)"
              required
              disabled={isLoading}
              className={errors.id ? "error" : ""}
            />
            {errors.id && <div className="field-error">{errors.id}</div>}
          </div>

          {/* 닉네임 입력 */}
          <div className="form-group">
            <label htmlFor="username">
              닉네임 <span className="required">*</span>
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="표시될 닉네임 (2-50자)"
              required
              disabled={isLoading}
              className={errors.username ? "error" : ""}
            />
            {errors.username && <div className="field-error">{errors.username}</div>}
          </div>

          {/* 비밀번호 입력 */}
          <div className="form-group">
            <label htmlFor="password">
              비밀번호 <span className="required">*</span>
            </label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="비밀번호 (8자 이상)"
                required
                disabled={isLoading}
                className={errors.password ? "error" : ""}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
                aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
            {errors.password && <div className="field-error">{errors.password}</div>}
          </div>

          {/* 비밀번호 확인 입력 */}
          <div className="form-group">
            <label htmlFor="confirmPassword">
              비밀번호 확인 <span className="required">*</span>
            </label>
            <div className="password-input-wrapper">
              <input
                type={showConfirmPassword ? "text" : "password"}
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="비밀번호를 다시 입력해주세요"
                required
                disabled={isLoading}
                className={errors.confirmPassword ? "error" : ""}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                disabled={isLoading}
                aria-label={showConfirmPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
              >
                {showConfirmPassword ? "🙈" : "👁️"}
              </button>
            </div>
            {errors.confirmPassword && <div className="field-error">{errors.confirmPassword}</div>}
          </div>

          {/* 이메일 입력 (선택 사항) */}
          <div className="form-group">
            <label htmlFor="email">
              이메일 <span className="optional">(선택 사항)</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="example@email.com"
              disabled={isLoading}
              className={errors.email ? "error" : ""}
            />
            {errors.email && <div className="field-error">{errors.email}</div>}
          </div>

          {/* 전체 에러 메시지 */}
          {errors.general && <div className="error-message">{errors.general}</div>}

          {/* 버튼 그룹 */}
          <div className="signup-btn-box">
            <button type="submit" className="signup-button" disabled={isLoading}>
              {isLoading ? "회원가입 중..." : "회원가입"}
            </button>
            <button
              type="button"
              className="cancel-button"
              onClick={handleCancel}
              disabled={isLoading}
            >
              취소
            </button>
          </div>
        </form>

        <div className="signup-footer">
          <p>
            이미 계정이 있으신가요?{" "}
            <button
              className="link-button"
              onClick={() => navigate('/login')}
              disabled={isLoading}
            >
              로그인하기
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default SignUpPage;
