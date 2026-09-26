import '@ant-design/v5-patch-for-react-19'
import 'normalize.css'
import { createRoot } from 'react-dom/client'
import './antd.scss'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(<App />)
