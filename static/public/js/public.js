document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const hamburger = document.querySelector('.header__hamburger');
    const mobileNav = document.querySelector('.header__nav');
    
    if (hamburger && mobileNav) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('is-active');
            mobileNav.classList.toggle('is-open');
            document.body.classList.toggle('no-scroll');
        });
    }

    // 2. Sticky Header on Scroll
    const header = document.querySelector('.header');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.classList.add('header--compact');
            } else {
                header.classList.remove('header--compact');
            }
        });
    }

    // 3. Accordion Logic
    const accordionHeaders = document.querySelectorAll('.accordion__header');
    
    accordionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const item = header.closest('.accordion__item');
            const content = item.querySelector('.accordion__content');
            const isActive = item.classList.contains('is-active');

            // Close all other accordions
            const parent = item.closest('.accordion');
            if (parent) {
                const allItems = parent.querySelectorAll('.accordion__item');
                allItems.forEach(i => {
                    i.classList.remove('is-active');
                    const c = i.querySelector('.accordion__content');
                    if (c) c.style.maxHeight = null;
                    i.querySelector('.accordion__header').setAttribute('aria-expanded', 'false');
                });
            }

            if (!isActive) {
                item.classList.add('is-active');
                content.style.maxHeight = content.scrollHeight + 'px';
                header.setAttribute('aria-expanded', 'true');
            }
        });
    });

    // 3b. Detail Accordion Logic with Smooth Scroll
    // Handle detail-faculty-item accordions
    const facultyAccordion = document.querySelector('.detail-faculties-accordion');
    if (facultyAccordion) {
        const facultyButtons = facultyAccordion.querySelectorAll('.detail-faculty-header');
        facultyButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Delay scroll to allow Alpine.js to update the DOM
                setTimeout(() => {
                    const item = button.closest('.detail-faculty-item');
                    if (item) {
                        // Scroll to the top of the accordion item with offset for header
                        const headerHeight = document.querySelector('.header')?.offsetHeight || 80;
                        const itemTop = item.getBoundingClientRect().top + window.scrollY - headerHeight - 20;
                        window.scrollTo({
                            top: itemTop,
                            behavior: 'smooth'
                        });
                    }
                }, 50);
            });
        });
    }

    // Handle detail-faq-item accordions
    const faqAccordion = document.querySelector('.detail-faq-accordion');
    if (faqAccordion) {
        const faqButtons = faqAccordion.querySelectorAll('.detail-faq-header');
        faqButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Delay scroll to allow Alpine.js to update the DOM
                setTimeout(() => {
                    const item = button.closest('.detail-faq-item');
                    if (item) {
                        // Scroll to the top of the accordion item with offset for header
                        const headerHeight = document.querySelector('.header')?.offsetHeight || 80;
                        const itemTop = item.getBoundingClientRect().top + window.scrollY - headerHeight - 20;
                        window.scrollTo({
                            top: itemTop,
                            behavior: 'smooth'
                        });
                    }
                }, 50);
            });
        });
    }

    // 4. Form Validation Enhancements
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('form-error')) {
                        errorMsg.style.display = 'block';
                    }
                } else {
                    field.classList.remove('is-invalid');
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('form-error')) {
                        errorMsg.style.display = 'none';
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
            } else {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('is-loading');
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span style="opacity:0.7">جاري الإرسال...</span>';
                    submitBtn.disabled = true;
                }
            }
        });

        // Clear error on input
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    input.classList.remove('is-invalid');
                    const errorMsg = input.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('form-error')) {
                        errorMsg.style.display = 'none';
                    }
                }
            });
        });
    });

    // 5. Scroll Reveal — cards, titles, accordions (scroll-triggered)
    const revealElements = document.querySelectorAll('.card, .stat-card, .section-title, .accordion__item');

    revealElements.forEach((el, index) => {
        el.classList.add('reveal-hidden');
        const delay = (index % 5) * 0.1;
        el.style.transitionDelay = `${delay}s`;
    });

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal-visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        rootMargin: '0px 0px -50px 0px',
        threshold: 0.1
    });

    revealElements.forEach(el => revealObserver.observe(el));

    // 5b. Hero content — fade-in stagger immediately on load (above the fold)
    const heroChildren = document.querySelectorAll('.hero__content > *');
    heroChildren.forEach((el, index) => {
        el.classList.add('reveal-hidden');
        el.style.transitionDelay = `${index * 0.12}s`;
        setTimeout(() => {
            el.classList.add('reveal-visible');
        }, 80);
    });

    // 6. Hero Layered Images — activate float loop exactly when entrance animation ends
    const circleImg = document.querySelector('.hero__circle-img');
    const studentsImg = document.querySelector('.hero__students-img');

    if (circleImg) {
        circleImg.addEventListener('animationend', () => {
            circleImg.classList.add('is-visible');
        }, { once: true });
    }

    if (studentsImg) {
        studentsImg.addEventListener('animationend', () => {
            studentsImg.classList.add('is-visible');
        }, { once: true });
    }
});
