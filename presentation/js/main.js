/**
 * 多模态图像修复程序 - 展示页面交互脚本
 * 提供导航、滚动、响应式等交互功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===== 移动端导航菜单切换 =====
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');

            // 切换菜单图标
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-bars')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // 点击导航链接后关闭移动端菜单
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                navToggle.querySelector('i').classList.remove('fa-times');
                navToggle.querySelector('i').classList.add('fa-bars');
            });
        });
    }

    // ===== 平滑滚动到锚点 =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // 计算导航栏高度
                const navbarHeight = document.querySelector('.navbar').offsetHeight;
                const targetPosition = targetElement.offsetTop - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ===== 滚动时高亮当前导航项 =====
    const sections = document.querySelectorAll('section[id]');
    const navItems = document.querySelectorAll('.nav-link');

    function highlightNavOnScroll() {
        let currentSectionId = '';

        // 找到当前视口中最顶部的部分
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            const navbarHeight = document.querySelector('.navbar').offsetHeight;

            if (window.scrollY >= (sectionTop - navbarHeight - 100)) {
                currentSectionId = section.getAttribute('id');
            }
        });

        // 更新导航链接的激活状态
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === `#${currentSectionId}`) {
                item.classList.add('active');
            }
        });
    }

    // 添加激活状态的CSS样式（通过JavaScript动态添加）
    const style = document.createElement('style');
    style.textContent = `
        .nav-link.active {
            color: var(--primary-color) !important;
            background-color: var(--bg-light) !important;
            font-weight: 600;
        }
    `;
    document.head.appendChild(style);

    // 初始高亮和滚动监听
    highlightNavOnScroll();
    window.addEventListener('scroll', highlightNavOnScroll);

    // ===== 滚动时显示/隐藏导航栏 =====
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');

    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop && scrollTop > 200) {
            // 向下滚动，隐藏导航栏
            navbar.style.transform = 'translateY(-100%)';
            navbar.style.transition = 'transform 0.3s ease';
        } else {
            // 向上滚动，显示导航栏
            navbar.style.transform = 'translateY(0)';
        }

        lastScrollTop = scrollTop;
    });

    // ===== 卡片悬停效果增强 =====
    const cards = document.querySelectorAll('.overview-card, .stack-item, .value-card, .deepdive-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.zIndex = '10';
        });

        card.addEventListener('mouseleave', function() {
            this.style.zIndex = '';
        });
    });

    // ===== 代码片段复制功能 =====
    const codeSnippets = document.querySelectorAll('.code-snippet');

    codeSnippets.forEach(snippet => {
        // 添加复制按钮
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<i class="far fa-copy"></i> 复制';
        copyButton.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 0.75rem;
            cursor: pointer;
            font-family: var(--font-sans);
            transition: all 0.2s ease;
        `;

        copyButton.addEventListener('mouseenter', function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
        });

        copyButton.addEventListener('mouseleave', function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
        });

        // 定位代码片段容器
        snippet.style.position = 'relative';
        snippet.appendChild(copyButton);

        // 复制功能
        copyButton.addEventListener('click', function() {
            const code = snippet.querySelector('code').innerText;
            navigator.clipboard.writeText(code).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> 已复制';
                this.style.background = 'rgba(16, 185, 129, 0.2)';
                this.style.borderColor = 'rgba(16, 185, 129, 0.5)';

                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.style.background = 'rgba(255, 255, 255, 0.1)';
                    this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                }, 2000);
            }).catch(err => {
                console.error('复制失败:', err);
                this.innerHTML = '<i class="fas fa-times"></i> 失败';
                this.style.background = 'rgba(239, 68, 68, 0.2)';
                this.style.borderColor = 'rgba(239, 68, 68, 0.5)';

                setTimeout(() => {
                    this.innerHTML = '<i class="far fa-copy"></i> 复制';
                    this.style.background = 'rgba(255, 255, 255, 0.1)';
                    this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                }, 2000);
            });
        });
    });

    // ===== 演讲模式支持（全屏和导航） =====
    // 添加演讲模式切换按钮
    const presentationButton = document.createElement('button');
    presentationButton.id = 'presentationMode';
    presentationButton.innerHTML = '<i class="fas fa-expand"></i> 演讲模式';
    presentationButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 20px;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.3s ease;
    `;

    document.body.appendChild(presentationButton);

    // 演讲模式状态
    let isPresentationMode = false;

    presentationButton.addEventListener('click', function() {
        isPresentationMode = !isPresentationMode;

        if (isPresentationMode) {
            // 进入演讲模式
            this.innerHTML = '<i class="fas fa-compress"></i> 退出演讲';
            this.style.background = 'var(--error-color)';

            // 隐藏导航栏和其他干扰元素
            navbar.style.display = 'none';
            document.querySelector('.footer').style.display = 'none';
            presentationButton.style.bottom = '10px';

            // 添加演讲控制
            addPresentationControls();

            // 进入全屏（如果支持）
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            }

            // 隐藏滚动条但不禁用滚动
            document.documentElement.style.overflow = 'hidden';
            document.body.style.overflow = 'hidden';

        } else {
            // 退出演讲模式
            this.innerHTML = '<i class="fas fa-expand"></i> 演讲模式';
            this.style.background = 'var(--primary-color)';

            // 恢复显示
            navbar.style.display = '';
            document.querySelector('.footer').style.display = '';
            presentationButton.style.bottom = '20px';

            // 移除演讲控制
            removePresentationControls();

            // 退出全屏
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }

            // 恢复滚动条
            document.documentElement.style.overflow = '';
            document.body.style.overflow = '';
        }
    });

    // 添加演讲控制功能
    function addPresentationControls() {
        // 添加上一页/下一页控制
        const controls = document.createElement('div');
        controls.id = 'presentationControls';
        controls.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        `;

        const prevButton = document.createElement('button');
        prevButton.innerHTML = '<i class="fas fa-arrow-left"></i> 上一节';
        prevButton.style.cssText = `
            background: rgba(255, 255, 255, 0.9);
            color: var(--text-primary);
            border: none;
            border-radius: 50px;
            padding: 10px 16px;
            font-size: 0.85rem;
            cursor: pointer;
            box-shadow: var(--shadow-md);
            display: flex;
            align-items: center;
            gap: 6px;
        `;

        const nextButton = document.createElement('button');
        nextButton.innerHTML = '下一节 <i class="fas fa-arrow-right"></i>';
        nextButton.style.cssText = prevButton.style.cssText;

        controls.appendChild(prevButton);
        controls.appendChild(nextButton);
        document.body.appendChild(controls);

        // 定义章节顺序
        const sectionsOrder = ['home', 'overview', 'tech', 'demo', 'deepdive', 'value'];
        let currentSectionIndex = 0;

        // 找到当前章节
        sections.forEach((section, index) => {
            const rect = section.getBoundingClientRect();
            if (rect.top >= 0 && rect.top < window.innerHeight / 2) {
                currentSectionIndex = sectionsOrder.indexOf(section.id);
            }
        });

        // 上一节功能
        prevButton.addEventListener('click', function() {
            if (currentSectionIndex > 0) {
                currentSectionIndex--;
                scrollToSection(sectionsOrder[currentSectionIndex]);
            }
        });

        // 下一节功能
        nextButton.addEventListener('click', function() {
            if (currentSectionIndex < sectionsOrder.length - 1) {
                currentSectionIndex++;
                scrollToSection(sectionsOrder[currentSectionIndex]);
            }
        });

        // 键盘控制
        document.addEventListener('keydown', function(e) {
            if (isPresentationMode) {
                if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
                    prevButton.click();
                } else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
                    nextButton.click();
                } else if (e.key === 'Escape') {
                    presentationButton.click();
                }
            }
        });

        // 滚动到指定章节
        function scrollToSection(sectionId) {
            const section = document.getElementById(sectionId);
            if (section) {
                const navbarHeight = 0; // 导航栏已隐藏
                const targetPosition = section.offsetTop - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        }
    }

    function removePresentationControls() {
        const controls = document.getElementById('presentationControls');
        if (controls) {
            controls.remove();
        }

        // 移除键盘事件监听
        document.removeEventListener('keydown', arguments.callee);
    }

    // ===== 页面加载动画 =====
    // 添加淡入效果
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';

    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);

    // 为卡片添加延迟动画
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';

        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 200 + index * 50);
    });

    // ===== 控制台欢迎信息 =====
    console.log('%c🎨 多模态图像修复程序展示页面',
        'color: #2563eb; font-size: 18px; font-weight: bold;');
    console.log('%c一个基于Python的多模态图像协同修复解决方案',
        'color: #4b5563; font-size: 14px;');
    console.log('%c欢迎查看项目展示！',
        'color: #10b981; font-size: 14px;');
});