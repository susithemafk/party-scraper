import { useState, useMemo, useCallback } from "react"
import axios from "axios"
import { ParserFunc, ScrapedItem } from "../types"

export const useScraper = (parserFunc: ParserFunc, initialUrl: string = "") => {
    const [url, setUrl] = useState<string>(initialUrl)
    const [htmlInput, setHtmlInput] = useState<string>("")
    const [rawResult, setRawResult] = useState<ScrapedItem[] | null>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const [copied, setCopied] = useState<boolean>(false)

    // Filter settings
    const [filterPast, setFilterPast] = useState<boolean>(true)
    const [onlyToday, setOnlyToday] = useState<boolean>(false)
    const [maxResults, setMaxResults] = useState<number>(4)

    const result = useMemo(() => {
        if (!rawResult) return null

        let processed = [...rawResult]
        const today = new Date().toISOString().split("T")[0]

        if (filterPast) {
            processed = processed.filter(item => !item.date || item.date >= today)
        }

        if (onlyToday) {
            processed = processed.filter(item => item.date === today)
        }

        if (maxResults > 0) {
            processed = processed.slice(0, maxResults)
        }

        return processed
    }, [rawResult, filterPast, onlyToday, maxResults])

    const handleFetchAndParse = useCallback(async () => {
        if (!url.trim()) return
        setLoading(true)
        setRawResult(null)

        try {
            const response = await axios.post("http://localhost:3001/fetch-html", { url })
            const html = response.data.html
            const data = parserFunc ? parserFunc(html) : []
            setRawResult(data)
        } catch (err: any) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert(`Fetch failed: ${msg}`)
        } finally {
            setLoading(false)
        }
    }, [url, parserFunc])

    const handleManualParse = useCallback(() => {
        if (!htmlInput.trim()) return
        const data = parserFunc ? parserFunc(htmlInput) : []
        setRawResult(data)
    }, [htmlInput, parserFunc])

    const handleCopy = useCallback(() => {
        if (!result) return
        navigator.clipboard.writeText(JSON.stringify(result, null, 4)).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }, [result])

    return {
        url,
        setUrl,
        htmlInput,
        setHtmlInput,
        result,
        loading,
        copied,
        filterPast,
        setFilterPast,
        onlyToday,
        setOnlyToday,
        maxResults,
        setMaxResults,
        handleFetchAndParse,
        handleManualParse,
        handleCopy,
    }
}
