import { useCallback, useMemo, useEffect } from "react"
import { useScraper } from "../hooks/useScraper"

export const ScraperSection = ({ title, defaultUrl, parserFunc, onResult, trigger = 0, onlyToday, setOnlyToday }) => {
    const { url, setUrl, htmlInput, setHtmlInput, result, loading, copied, handleFetchAndParse, handleManualParse, handleCopy } = useScraper(
        parserFunc,
        defaultUrl,
        null, // We handle onResult manually to support filtering
        trigger
    )

    const filteredResult = useMemo(() => {
        if (!result) return null
        if (!onlyToday) return result

        const todayStr = new Date().toISOString().split("T")[0]
        return result.filter((item) => item.date === todayStr)
    }, [result, onlyToday])

    // Sync with parent state
    useEffect(() => {
        if (onResult && filteredResult !== null) {
            onResult(title, filteredResult)
        }
    }, [filteredResult, title, onResult])

    return (
        <div className="scraper-section" style={{
            borderColor: result && filteredResult && filteredResult.length === 0 ? "#ef4444" : ""
        }}>
            <h2 className="section-title" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                {title}
                <label style={{ fontSize: "0.7rem", fontWeight: "normal", display: "flex", alignItems: "center", gap: "5px", cursor: "pointer" }}>
                    <input
                        type="checkbox"
                        checked={onlyToday}
                        onChange={(e) => setOnlyToday(e.target.checked)}
                    />
                    Only Today
                </label>
            </h2>

            <div className="input-group">
                <div className="field-label">AUTOMATIC URL:</div>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "0.8rem" }}>
                    <input type="text" placeholder="Enter website URL..." value={url} onChange={(e) => setUrl(e.target.value)} />
                </div>
                <div className="button-group">
                    <button onClick={handleFetchAndParse} disabled={loading} style={{ flex: 1 }}>
                        {loading && <span className="loader"></span>}
                        Fetch & Find
                    </button>
                </div>
            </div>

            {filteredResult && (
                <div className="results-section">
                    <div className="field-label result">
                        RESULT ARRAY ({filteredResult.length}):
                        <button className="copy-btn" onClick={handleCopy} style={{ background: copied ? "var(--success)" : "" }}>
                            {copied ? "Copied!" : "Copy to Clipboard"}
                        </button>
                    </div>
                    {filteredResult.length === 0 && (
                        <div style={{ color: "#ef4444", fontSize: "0.8rem", marginBottom: "5px", fontWeight: "bold" }}>
                            ⚠️ No events found for today.
                        </div>
                    )}
                    <textarea readOnly value={JSON.stringify(filteredResult, null, 4)} />
                </div>
            )}
        </div>
    )
}
