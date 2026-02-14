import { useState } from "react"
import axios from "axios"

export const useScraper = (parserFunc, initialUrl = "") => {
    const [url, setUrl] = useState(initialUrl)
    const [htmlInput, setHtmlInput] = useState("")
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [copied, setCopied] = useState(false)

    const handleFetchAndParse = async () => {
        if (!url.trim()) return
        setLoading(true)
        setResult(null)

        try {
            const response = await axios.post("http://localhost:3001/fetch-html", { url })
            const html = response.data.html
            const data = parserFunc ? parserFunc(html) : null
            setResult(data)
        } catch (err) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert(`Fetch failed: ${msg}`)
        } finally {
            setLoading(false)
        }
    }

    const handleManualParse = () => {
        if (!htmlInput.trim()) return
        const data = parserFunc ? parserFunc(htmlInput) : null
        setResult(data)
    }

    const handleCopy = () => {
        if (!result) return
        navigator.clipboard.writeText(JSON.stringify(result, null, 4)).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }

    return {
        url,
        setUrl,
        htmlInput,
        setHtmlInput,
        result,
        loading,
        copied,
        handleFetchAndParse,
        handleManualParse,
        handleCopy,
    }
}
