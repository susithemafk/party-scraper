import React, { useState } from "react"
import axios from "axios"

export const InstagramLogin: React.FC = () => {
    const [loginMethod, setLoginMethod] = useState<"credentials" | "session">("credentials")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [sessionId, setSessionId] = useState("")
    const [verificationCode, setVerificationCode] = useState("")
    const [isChallenge, setIsChallenge] = useState(false)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<{ success: boolean; message: string; user?: any } | null>(null)

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setResult(null)

        try {
            const payload: any = loginMethod === "credentials" ? { email, password } : { session_id: sessionId }

            if (isChallenge) {
                payload.verification_code = verificationCode
                // When resolving challenge, we need to send the email/pass too
                // because the backend 'cl' instance might have reset
                payload.email = email
                payload.password = password
            }

            const response = await axios.post("http://localhost:8000/ig-login", payload)

            if (response.data.status === "challenge") {
                setIsChallenge(true)
                setResult({
                    success: true,
                    message: response.data.message,
                })
            } else {
                setIsChallenge(false)
                setResult({
                    success: true,
                    message: response.data.message,
                    user: response.data.user,
                })
            }
        } catch (err: any) {
            let errorMsg = "Login failed"

            if (err.response?.data?.detail) {
                const detail = err.response.data.detail
                if (typeof detail === "string") {
                    errorMsg = detail
                } else if (Array.isArray(detail)) {
                    // FastAPI validation errors (422) are arrays
                    errorMsg = "Validation Error: " + detail.map(d => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join(", ")
                    errorMsg += ". Make sure to RESTART your backend server!"
                } else {
                    errorMsg = JSON.stringify(detail)
                }
            } else if (err.message) {
                errorMsg = err.message
            }

            setResult({
                success: false,
                message: errorMsg,
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="scraper-section" style={{ border: "1px solid #E1306C", background: "rgba(225, 48, 108, 0.05)" }}>
            <h2 className="section-title" style={{ borderBottomColor: "#E1306C" }}>
                <i className="bi bi-instagram"></i> Instagram Login
            </h2>

            {!isChallenge && (
                <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
                    <button
                        onClick={() => setLoginMethod("credentials")}
                        style={{
                            flex: 1,
                            background: loginMethod === "credentials" ? "#E1306C" : "transparent",
                            border: "1px solid #E1306C",
                            fontSize: "0.8rem",
                            padding: "0.5rem",
                            color: "white",
                        }}
                    >
                        Email + Password
                    </button>
                    <button
                        onClick={() => setLoginMethod("session")}
                        style={{
                            flex: 1,
                            background: loginMethod === "session" ? "#E1306C" : "transparent",
                            border: "1px solid #E1306C",
                            fontSize: "0.8rem",
                            padding: "0.5rem",
                            color: "white",
                        }}
                    >
                        Session ID (Safe)
                    </button>
                </div>
            )}

            <form onSubmit={handleLogin} className="input-group">
                {isChallenge ? (
                    <>
                        <div className="field-label" style={{ color: "#f09433" }}>
                            VERIFICATION CODE:
                        </div>
                        <input
                            type="text"
                            value={verificationCode}
                            onChange={(e) => setVerificationCode(e.target.value)}
                            placeholder="Enter 6-digit code from email"
                            disabled={loading}
                            style={{ marginBottom: "1.5rem", borderColor: "#f09433" }}
                        />
                    </>
                ) : loginMethod === "credentials" ? (
                    <>
                        <div className="field-label">EMAIL:</div>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Instagram Email"
                            autoComplete="email"
                            disabled={loading}
                            style={{ marginBottom: "1rem" }}
                        />

                        <div className="field-label">PASSWORD:</div>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Instagram Password"
                            autoComplete="current-password"
                            disabled={loading}
                            style={{ marginBottom: "1.5rem" }}
                        />
                    </>
                ) : (
                    <>
                        <div className="field-label">SESSION ID:</div>
                        <input
                            type="text"
                            value={sessionId}
                            onChange={(e) => setSessionId(e.target.value)}
                            placeholder="Get from browser cookies (sessionid)"
                            disabled={loading}
                            style={{ marginBottom: "1rem" }}
                        />
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "1.5rem" }}>
                            Go to Instagram.com &gt; F12 &gt; Application (Storage) &gt; Cookies &gt; Copy value of 'sessionid'
                        </div>
                    </>
                )}

                <button
                    type="submit"
                    disabled={loading || (isChallenge ? !verificationCode : loginMethod === "credentials" ? !email || !password : !sessionId)}
                    style={{
                        background: isChallenge ? "#f09433" : "linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%)",
                        width: "100%",
                        padding: "1rem",
                    }}
                >
                    {loading ? "Processing..." : isChallenge ? "Verify Code" : "Login to Instagram"}
                </button>

                {isChallenge && (
                    <button
                        type="button"
                        onClick={() => setIsChallenge(false)}
                        style={{
                            width: "100%",
                            marginTop: "0.5rem",
                            background: "transparent",
                            border: "none",
                            fontSize: "0.8rem",
                            color: "var(--text-muted)",
                        }}
                    >
                        Cancel and try again
                    </button>
                )}

                {result && (
                    <div
                        style={{
                            padding: "1rem",
                            borderRadius: "8px",
                            background: result.success ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)",
                            border: `1px solid ${result.success ? "var(--success)" : "#ef4444"}`,
                            textAlign: "left",
                        }}
                    >
                        <div style={{ fontWeight: "bold", color: result.success ? "var(--success)" : "#ef4444", marginBottom: "0.5rem" }}>
                            {result.success ? "✓ Success" : "✗ Error"}
                        </div>
                        <div style={{ fontSize: "0.9rem", color: "var(--text)" }}>{result.message}</div>
                        {result.user && (
                            <pre style={{ fontSize: "0.7rem", marginTop: "1rem", background: "rgba(0,0,0,0.2)", padding: "0.5rem" }}>
                                {JSON.stringify(result.user, null, 2)}
                            </pre>
                        )}
                    </div>
                )}
            </form>
        </div>
    )
}
