import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import EvalSetsPage from './pages/EvalSetsPage'
import EvalDataPage from './pages/EvalDataPage'
import ResultsSetPage from './pages/ResultsSetPage'
import ResultsDataPage from './pages/ResultsDataPage'
import MultiExecutePage from './pages/MultiExecutePage'
import ConfigPage from './pages/ConfigPage'
import RootLayout from './layout/RootLayout'

export default function App() {
  return (
    <RootLayout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/sets" element={<EvalSetsPage />} />
        <Route path="/set/:id" element={<EvalDataPage />} />
        <Route path="/results/set/:id" element={<ResultsSetPage />} />
  <Route path="/results/data/:setId/:corpusId" element={<ResultsDataPage />} />
        <Route path="/multi-execute" element={<MultiExecutePage />} />
  <Route path="/config" element={<ConfigPage />} />
      </Routes>
    </RootLayout>
  )
}
