import React from "react"
import "./App.css"
import { ScraperSection } from "./components/ScraperSection"
import { artbarParser } from "./parsers/artbar"
import { kabinetParser } from "./parsers/kabinet"

const App: React.FC = () => {
    return (
        <div className="container">
            <h1>Party Scraper</h1>
            <p className="subtitle">Automated Event Intelligence</p>

            <div className="main-content">
                <ScraperSection
                    title="Kabinet Múz"
                    defaultUrl="https://www.kabinetmuz.cz/program"
                    parserFunc={kabinetParser}
                />

                <ScraperSection
                    title="Artbar Club"
                    defaultUrl="https://www.artbar.club/shows"
                    parserFunc={artbarParser}
                />
            </div>
        </div>
    )
}

export default App
