import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import StoryLoader from './components/StoryLoader'
import StoryGenerator from './components/StoryGenerator'

function App() {
  return (
    <BrowserRouter>
      <div className='app-container'>
        <header>
          <h1>Interactive story generator</h1>
        </header>
        <main>
          <Routes>
            <Route path='/' element={<StoryGenerator />} />
            <Route path='/story/:id' element={<StoryLoader />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
