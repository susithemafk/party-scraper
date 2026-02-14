import { useState } from "react"
import axios from "axios"
import { ParserFunc, ScrapedItem } from "../types"

export const useScraper = (parserFunc: ParserFunc, initialUrl: string = "", onResult: ((data: ScrapedItem[]) => void) | null = null) => {
    const [url, setUrl] = useState<string>(initialUrl)
    const [htmlInput, setHtmlInput] = useState<string>("")
    const [result, setResult] = useState<ScrapedItem[] | null>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const [copied, setCopied] = useState<boolean>(false)

    const handleFetchAndParse = async () => {
        if (!url.trim()) return
        setLoading(true)
        setResult(null)

        try {
            const response = await axios.post("http://localhost:3001/fetch-html", { url })
            const html = response.data.html
            const data = parserFunc ? parserFunc(html) : []
            setResult(data)
            if (onResult && data.length > 0) onResult(data)
        } catch (err: any) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert(`Fetch failed: ${msg}`)
        } finally {
            setLoading(false)
        }
    }

    const handleManualParse = () => {
        if (!htmlInput.trim()) return
        const data = parserFunc ? parserFunc(htmlInput) : []
        setResult(data)
        if (onResult && data.length > 0) onResult(data)
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
