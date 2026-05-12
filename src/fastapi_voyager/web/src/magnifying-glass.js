/**
 * Magnifying Glass for SVG Graph Visualization
 *
 * Provides a circular magnifying glass effect that follows the mouse cursor.
 * Activated by pressing the Space key.
 *
 * Usage:
 *   const magnifier = new MagnifyingGlass(svgElement, {
 *     magnification: 2.0
 *   })
 *
 * The lens radius is automatically calculated based on viewBox width.
 */

export class MagnifyingGlass {
  // Class constants
  static DEFAULT_MAGNIFICATION = 2.0
  static RADIUS_PERCENTAGE = 0.2 // Percentage of viewBox width
  static LENS_OFFSET = 10 // 放大镜相对于鼠标的偏移量
  static BORDER_WIDTH = 2 // 边框宽度
  static UPDATE_THROTTLE_MS = 16 // 更新节流（约60fps）

  /**
   * Extract viewBox dimensions from SVG element (called dynamically each time)
   * @private
   */
  _getViewBoxDimensions() {
    const viewBoxAttr = this.svg.getAttribute("viewBox")
    if (viewBoxAttr) {
      const parts = viewBoxAttr.trim().split(/\s+/)
      if (parts.length === 4) {
        const [, , width, height] = parts.map(parseFloat)
        if (!isNaN(width) && !isNaN(height) && width > 0 && height > 0) {
          return { width, height }
        }
      }
    }
    // Fallback to getBoundingClientRect if no viewBox
    const rect = this.svg.getBoundingClientRect()
    return { width: rect.width || 1000, height: rect.height || 1000 }
  }

  /**
   * Get current radius (dynamically calculated based on current viewBox width)
   * @returns {number} Radius in SVG units
   */
  get radius() {
    const { width } = this._getViewBoxDimensions()
    return Math.round(width * MagnifyingGlass.RADIUS_PERCENTAGE)
  }

  /**
   * @param {SVGElement} svgElement - The SVG element to magnify
   * @param {Object} options - Configuration options
   * @param {number} options.magnification - Zoom level (default: 2.0)
   * @param {boolean} options.debug - Enable debug logging (default: false)
   */
  constructor(svgElement, options = {}) {
    // Validate SVG element
    if (!svgElement || !(svgElement instanceof SVGElement)) {
      throw new Error("[MagnifyingGlass] Invalid SVG element provided")
    }

    this.svg = svgElement

    // Calculate magnification
    this._magnification = this._validateNumber(
      options.magnification,
      MagnifyingGlass.DEFAULT_MAGNIFICATION,
      0.1,
      10
    )

    this.debug = options.debug || false
    this.active = false

    // Throttle updates for performance
    this._pendingUpdate = false
    this._lastPosition = null

    // Content caching for performance
    this._cachedContent = null
    this._contentDirty = true

    this._initLens()
    this._bindEvents()
  }

  /**
   * Get current magnification
   */
  get magnification() {
    return this._magnification
  }

  /**
   * Set magnification and update lens if active
   * @param {number} value - New magnification value
   */
  set magnification(value) {
    const validated = this._validateNumber(value, MagnifyingGlass.DEFAULT_MAGNIFICATION, 0.1, 10)
    if (validated !== this._magnification) {
      this._magnification = validated
      this._log("Magnification updated to:", validated)

      // 如果放大镜当前激活，立即更新显示
      if (this.active && this._lastPosition) {
        this._updateTransform(this._lastPosition.x, this._lastPosition.y)
      }
    }
  }

  /**
   * Validate and sanitize number input
   * @param {*} value - Value to validate
   * @param {number} defaultValue - Default value if invalid
   * @param {number} min - Minimum allowed value
   * @param {number} max - Maximum allowed value
   * @returns {number} Validated number
   * @private
   */
  _validateNumber(value, defaultValue, min, max) {
    if (typeof value !== "number" || isNaN(value)) {
      return defaultValue
    }
    return Math.max(min, Math.min(max, value))
  }

  /**
   * Internal logging method
   * @private
   */
  _log(...args) {
    if (this.debug) {
      console.log("[MagnifyingGlass]", ...args)
    }
  }

  /**
   * Initialize the lens SVG elements
   * @private
   */
  _initLens() {
    this._log("Initializing lens...")
    // 1. Create defs and clipPath
    const defs = d3.select(this.svg).append("defs")
    this.clipPathId = `lens-clip-${Math.random().toString(36).substr(2, 9)}`
    this._log("clipPathId:", this.clipPathId)

    defs
      .append("clipPath")
      .attr("id", this.clipPathId)
      .append("circle")
      .attr("r", this.radius)
      .attr("cx", 0)
      .attr("cy", 0)

    // 2. Create lens group (initially hidden)
    this.lensGroup = d3
      .select(this.svg)
      .append("g")
      .attr("class", "magnifying-lens")
      .style("display", "none")

    // 3. Create lens border circle
    this.lensGroup
      .append("circle")
      .attr("class", "lens-border")
      .attr("r", this.radius + MagnifyingGlass.BORDER_WIDTH)
      .attr("fill", "rgba(255,255,255,0.95)")
      .attr("stroke", "#999")
      .attr("stroke-width", MagnifyingGlass.BORDER_WIDTH)
      .attr("cx", 0) // Initialize at origin, will be updated on mouse move
      .attr("cy", 0)

    // 4. Create clipped content group
    this.lensContent = this.lensGroup
      .append("g")
      .attr("clip-path", `url(#${this.clipPathId})`)
      .append("g")
      .attr("class", "lens-content")

    this._log("Lens initialized successfully")
  }

  /**
   * Bind keyboard and mouse events
   * @private
   */
  _bindEvents() {
    // Space key to toggle
    this._handleKeyDown = (e) => {
      if (e.code === "Space" && !e.repeat) {
        e.preventDefault()
        this._log("Space pressed, activating...")
        this.toggle()
      }
    }

    this._handleKeyUp = (e) => {
      if (e.code === "Space") {
        this._log("Space released, deactivating...")
        this.deactivate()
      }
    }

    this._handleMouseMove = (e) => {
      // 记录最后鼠标位置，用于第一次激活时的位置计算
      const rect = this.svg.getBoundingClientRect()
      this._lastMousePos = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }

      if (this.active) {
        this._updatePosition(e)
      }
    }

    this._handleClick = (e) => {
      if (this.active) {
        this._log("Clicked, deactivating...")
        this.deactivate()
      }
    }

    document.addEventListener("keydown", this._handleKeyDown)
    document.addEventListener("keyup", this._handleKeyUp)
    this.svg.addEventListener("mousemove", this._handleMouseMove)
    this.svg.addEventListener("click", this._handleClick)

    this._log("Events bound successfully")
  }

  /**
   * Update lens position and content based on mouse position
   * @private
   */
  _updatePosition(event) {
    // Use requestAnimationFrame for smooth performance
    if (this._pendingUpdate) return

    this._pendingUpdate = true
    requestAnimationFrame(() => {
      this._performUpdate(event)
      this._pendingUpdate = false
    })
  }

  /**
   * Perform the actual position update
   * @private
   */
  _performUpdate(event) {
    try {
      // 使用 SVG 标准的坐标转换方法，代替 getBoundingClientRect()
      const pt = this.svg.createSVGPoint()
      pt.x = event.clientX
      pt.y = event.clientY

      let svgP
      try {
        // 转换为 SVG 坐标（考虑 SVG 内部所有变换）
        const ctm = this.svg.getScreenCTM()
        if (!ctm || !ctm.inverse) {
          // 如果 getScreenCTM() 失败，退回到简单方法
          const rect = this.svg.getBoundingClientRect()
          svgP = {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
          }
        } else {
          svgP = pt.matrixTransform(ctm.inverse())
        }
      } catch (e) {
        // 容错处理
        const rect = this.svg.getBoundingClientRect()
        svgP = {
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        }
      }

      // Get current radius (dynamically calculated from viewBox)
      const currentRadius = this.radius

      // 调整放大镜位置，使其在鼠标上方，靠近下方边缘外侧
      // 偏移量：向下一点，让鼠标位于放大镜底部边缘外侧
      const offsetX = 0
      const offsetY = currentRadius + MagnifyingGlass.LENS_OFFSET // 放大镜半径 + 偏移量

      const lensX = svgP.x + offsetX
      const lensY = svgP.y - offsetY // 向上偏移

      // Move lens group to adjusted position
      this.lensGroup.attr("transform", `translate(${lensX}, ${lensY})`)

      // 计算相对于 lensGroup 的坐标
      const relativeCX = svgP.x - lensX
      const relativeCY = svgP.y - lensY

      // Update clipPath circle radius and position (radius is dynamic now)
      d3.select(`#${this.clipPathId} circle`)
        .attr("r", currentRadius)
        .attr("cx", relativeCX)
        .attr("cy", relativeCY)

      // Update lens border circle radius and position
      this.lensGroup
        .select(".lens-border")
        .attr("r", currentRadius + MagnifyingGlass.BORDER_WIDTH)
        .attr("cx", relativeCX)
        .attr("cy", relativeCY)

      // Update magnified content with absolute coordinates
      this._updateContent(svgP.x, svgP.y)
    } catch (error) {
      this._log("Error in _performUpdate:", error)
      // 发生错误时停用放大镜，避免持续出错
      this.deactivate()
    }
  }

  /**
   * Update the magnified content
   * @param {number} absoluteX - Absolute X coordinate in SVG space
   * @param {number} absoluteY - Absolute Y coordinate in SVG space
   * @private
   */
  _updateContent(absoluteX, absoluteY) {
    // Use D3 selection (don't convert to DOM node)
    const mainGroup = d3.select(this.svg).select("g")
    if (mainGroup.empty()) return

    // 只在首次或内容变化时克隆
    if (!this._cachedContent || this._contentDirty) {
      this.lensContent.html("")
      const clonedContent = mainGroup.clone(true).node()
      this.lensContent.node().appendChild(clonedContent)
      this._cachedContent = clonedContent
      this._contentDirty = false
      this._log("Content cloned and cached")
    }

    // 只更新 transform
    this._updateTransform(absoluteX, absoluteY)
  }

  /**
   * Update the transform of lens content
   * @param {number} absoluteX - Absolute X coordinate in SVG space
   * @param {number} absoluteY - Absolute Y coordinate in SVG space
   * @private
   */
  _updateTransform(absoluteX, absoluteY) {
    const scale = this.magnification
    const currentRadius = this.radius
    const offsetY = currentRadius + MagnifyingGlass.LENS_OFFSET

    // 正确的公式:
    // tx = -scale * absoluteX (让 absoluteX 变换后对应 x=0)
    // ty = offsetY - scale * absoluteY (让 absoluteY 变换后对应 y=offsetY，即 clipPath 圆心)
    const transform = `translate(${-scale * absoluteX}, ${offsetY - scale * absoluteY}) scale(${scale})`
    this.lensContent.attr("transform", transform)

    this._lastPosition = { x: absoluteX, y: absoluteY }
  }

  /**
   * Activate the magnifying glass
   */
  activate() {
    this._log("Activating magnifier...")
    this.active = true
    this._contentDirty = true // 标记内容为脏，激活时会重新克隆
    this.lensGroup.style("display", null)
    d3.select(this.svg).classed("magnifier-active", true)

    // 解决第一次激活时的位置问题
    // 获取当前鼠标位置并立即更新内容
    this._updateContentFromCurrentMouse()
  }

  // 获取当前鼠标位置（跨浏览器兼容）
  _getCurrentMousePosition() {
    if (typeof this._lastMousePos !== "undefined") {
      return this._lastMousePos
    }

    // 作为备用方案，如果没有记录位置，返回 SVG 中心
    const rect = this.svg.getBoundingClientRect()
    return { x: rect.width / 2, y: rect.height / 2 }
  }

  // 使用当前鼠标位置更新内容
  _updateContentFromCurrentMouse() {
    const currentMousePos = this._getCurrentMousePosition()
    if (currentMousePos) {
      // 模拟事件对象
      this._performUpdate({
        clientX: currentMousePos.x + this.svg.getBoundingClientRect().left,
        clientY: currentMousePos.y + this.svg.getBoundingClientRect().top,
      })
    }
  }

  /**
   * Deactivate the magnifying glass
   */
  deactivate() {
    this._log("Deactivating magnifier...")
    this.active = false
    this.lensGroup.style("display", "none")
    d3.select(this.svg).classed("magnifier-active", false)
    this._lastPosition = null
  }

  /**
   * Toggle magnifying glass on/off
   */
  toggle() {
    this.active ? this.deactivate() : this.activate()
  }

  /**
   * Clean up and remove lens elements
   */
  destroy() {
    this._log("Destroying...")
    // Remove event listeners
    document.removeEventListener("keydown", this._handleKeyDown)
    document.removeEventListener("keyup", this._handleKeyUp)
    this.svg.removeEventListener("mousemove", this._handleMouseMove)
    this.svg.removeEventListener("click", this._handleClick)

    // Clean up DOM elements
    if (this.lensGroup) this.lensGroup.remove()
    const defs = d3.select(this.svg).select("defs")
    if (defs) defs.select(`#${this.clipPathId}`).remove()

    // Clean up references
    this._cachedContent = null
    this.lensGroup = null
    this.lensContent = null
    this.svg = null
  }
}
