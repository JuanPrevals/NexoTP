import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

const BACKEND_PREFIX = '/backend-page'

function parsePage(markup) {
  const documentNode = new DOMParser().parseFromString(markup, 'text/html')
  return {
    title: documentNode.title || 'NexoTP',
    topbar: documentNode.querySelector('.topbar')?.outerHTML || '',
    flashes: documentNode.querySelector('.flash-stack')?.outerHTML || '',
    main: documentNode.querySelector('main')?.innerHTML || markup,
    bodyAttributes: Object.fromEntries(
      [...documentNode.body.attributes].map(({ name, value }) => [name, value]),
    ),
  }
}

function backendUrl(pathname, search = '') {
  return `${BACKEND_PREFIX}${pathname}${search}`
}

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const containerRef = useRef(null)
  const [page, setPage] = useState(null)
  const [error, setError] = useState('')

  const renderResponse = useCallback(async (response) => {
    if (!response.ok && response.status >= 500) throw new Error(`Servidor: ${response.status}`)
    const nextPage = parsePage(await response.text())
    document.title = nextPage.title
    setPage(nextPage)
    setError('')
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    fetch(backendUrl(location.pathname, location.search), {
      credentials: 'include',
      signal: controller.signal,
      headers: { 'X-Requested-With': 'react' },
    })
      .then(renderResponse)
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') setError('No se pudo conectar con la API de NexoTP.')
      })
    return () => controller.abort()
  }, [location.pathname, location.search, renderResponse])

  useEffect(() => {
    const handleClick = async (event) => {
      const navButton = event.target.closest('[data-nav-toggle]')
      if (navButton) {
        const navigation = containerRef.current?.querySelector('#site-navigation')
        const isOpen = navButton.getAttribute('aria-expanded') === 'true'
        navButton.setAttribute('aria-expanded', String(!isOpen))
        navButton.querySelector('.visually-hidden').textContent = isOpen ? 'Abrir menu' : 'Cerrar menu'
        navigation?.classList.toggle('is-open', !isOpen)
        return
      }

      const themeButton = event.target.closest('[data-theme-toggle]')
      if (themeButton) {
        const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'
        document.documentElement.dataset.theme = nextTheme
        localStorage.setItem('theme', nextTheme)
        return
      }

      const applyButton = event.target.closest('[data-apply]')
      if (applyButton) {
        event.preventDefault()
        applyButton.disabled = true
        applyButton.textContent = 'Enviando'
        try {
          const response = await fetch(backendUrl(`/postular/${applyButton.dataset.apply}`), {
            method: 'POST',
            credentials: 'include',
            headers: { 'X-Requested-With': 'fetch' },
          })
          const result = await response.json()
          applyButton.textContent = result.ok ? 'Postulado' : result.message || 'No enviado'
          if (result.ok) {
            applyButton.classList.remove('btn-primary')
            applyButton.classList.add('btn-secondary')
          } else {
            applyButton.disabled = false
          }
        } catch {
          applyButton.disabled = false
          applyButton.textContent = 'Reintentar'
        }
        return
      }

      const link = event.target.closest('a[href]')
      if (!link || link.target || link.hasAttribute('download')) return
      const url = new URL(link.href, window.location.origin)
      if (url.origin !== window.location.origin || url.pathname.endsWith('.pdf') || url.pathname.endsWith('.csv')) return
      event.preventDefault()
      const navigation = containerRef.current?.querySelector('#site-navigation')
      const closeNavButton = containerRef.current?.querySelector('[data-nav-toggle]')
      navigation?.classList.remove('is-open')
      closeNavButton?.setAttribute('aria-expanded', 'false')
      navigate(`${url.pathname}${url.search}`)
    }

    const handleSubmit = async (event) => {
      const form = event.target.closest('form')
      if (!form) return
      event.preventDefault()
      const submitter = event.submitter
      if (form.onsubmit && !form.onsubmit(event)) return
      if (submitter) submitter.disabled = true
      try {
        const method = (form.method || 'get').toUpperCase()
        const data = new FormData(form)
        const action = new URL(form.action || window.location.href)
        let requestUrl = backendUrl(action.pathname, action.search)
        const options = { method, credentials: 'include', headers: { 'X-Requested-With': 'react' } }
        if (method === 'GET') {
          const query = new URLSearchParams(data)
          requestUrl = backendUrl(action.pathname, query.toString() ? `?${query}` : '')
        } else {
          options.body = data
        }
        const response = await fetch(requestUrl, options)
        const finalUrl = new URL(response.url)
        const finalPath = finalUrl.pathname.replace(/^\/backend-page/, '') || '/'
        await renderResponse(response)
        if (`${finalPath}${finalUrl.search}` !== `${location.pathname}${location.search}`) {
          navigate(`${finalPath}${finalUrl.search}`, { replace: true })
        }
      } catch {
        setError('No fue posible completar la accion. Intenta nuevamente.')
      } finally {
        if (submitter) submitter.disabled = false
      }
    }

    const container = containerRef.current
    container?.addEventListener('click', handleClick)
    container?.addEventListener('submit', handleSubmit)
    return () => {
      container?.removeEventListener('click', handleClick)
      container?.removeEventListener('submit', handleSubmit)
    }
  }, [location.pathname, location.search, navigate, renderResponse])

  useEffect(() => {
    document.documentElement.dataset.theme = localStorage.getItem('theme') || 'light'
  }, [])

  if (error) return <main className="page"><div className="empty-state"><h1>Conexion interrumpida</h1><p>{error}</p></div></main>
  if (!page) return <div className="react-loading" role="status" aria-live="polite"><span className="spinner-border" /><span className="visually-hidden">Cargando</span></div>

  return (
    <div ref={containerRef} {...page.bodyAttributes}>
      <a className="skip-link" href="#contenido-principal">Saltar al contenido</a>
      <div dangerouslySetInnerHTML={{ __html: page.topbar }} />
      <div dangerouslySetInnerHTML={{ __html: page.flashes }} />
      <main id="contenido-principal" dangerouslySetInnerHTML={{ __html: page.main }} />
    </div>
  )
}
