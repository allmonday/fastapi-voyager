/**
 * Service Worker for fastapi-voyager
 *
 * Provides caching for CDN and local static resources.
 * Uses version-based cache management - old caches are cleaned on version update.
 */

const CACHE_PREFIX = "fastapi-voyager-v"
const VERSION = "<!-- VERSION_PLACEHOLDER -->"
const CACHE_NAME = CACHE_PREFIX + VERSION
const STATIC_PATH = "<!-- STATIC_PATH -->"

// CDN resources to cache (cache-first strategy)
const CDN_ASSETS = [
  "https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/jquery.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
  "https://unpkg.com/@hpcc-js/wasm@2.20.0/dist/graphviz.umd.js",
  "https://cdnjs.cloudflare.com/ajax/libs/d3-graphviz/5.6.0/d3-graphviz.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/jquery-mousewheel/3.1.13/jquery.mousewheel.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/jquery-color/2.1.2/jquery.color.min.js",
  "https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900|Material+Icons",
  "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css",
]

// CDN domains for dynamic matching (catches all resources from these domains)
const CDN_DOMAINS = [
  "unpkg.com",
  "cdnjs.cloudflare.com",
  "cdn.jsdelivr.net",
  "fonts.googleapis.com",
  "fonts.gstatic.com",
]

/**
 * Install event - pre-cache CDN resources
 * Uses Promise.allSettled to handle individual CDN failures gracefully
 */
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        CDN_ASSETS.map((url) =>
          cache.add(new Request(url, { mode: "cors" })).catch(() => {
            // Silently fail for individual CDN resources
            console.log("[Voyager SW] Failed to cache:", url)
          })
        )
      )
    })
  )
  // Activate immediately without waiting for existing clients to close
  self.skipWaiting()
})

/**
 * Activate event - clean up old version caches
 */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
          .map((name) => {
            console.log("[Voyager SW] Deleting old cache:", name)
            return caches.delete(name)
          })
      )
    })
  )
  // Take control of all clients immediately
  self.clients.claim()
})

/**
 * Fetch event - implement caching strategies
 */
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url)

  // Local static resources: stale-while-revalidate
  // Returns cached version immediately, updates cache in background
  if (url.pathname.includes("fastapi-voyager-static")) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          const fetchPromise = fetch(event.request)
            .then((networkResponse) => {
              if (networkResponse.ok) {
                cache.put(event.request, networkResponse.clone())
              }
              return networkResponse
            })
            .catch(() => cachedResponse)

          return cachedResponse || fetchPromise
        })
      })
    )
    return
  }

  // CDN resources: cache-first strategy
  // Match by domain to catch all CDN resources (including dynamic imports)
  const isCdnRequest = CDN_DOMAINS.some((domain) => url.hostname === domain)
  if (isCdnRequest) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          console.log("[Voyager SW] Cache hit:", event.request.url)
          return cachedResponse
        }
        console.log("[Voyager SW] Cache miss, fetching:", event.request.url)
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse.ok) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, networkResponse.clone())
            })
          }
          return networkResponse
        })
      })
    )
    return
  }

  // API requests: network-only (no caching)
  // These are dynamic and should always be fresh
  const apiEndpoints = [
    "/dot",
    "/source",
    "/vscode-link",
    "/er-diagram",
    "/dot-search",
    "/dot-core-data",
    "/dot-render-core-data",
  ]
  if (apiEndpoints.some((p) => url.pathname.endsWith(p))) {
    return // Let the browser handle it normally
  }
})
