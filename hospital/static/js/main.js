"use strict";

/* -----------------------------
   CUSTOM SCROLL ANIMATIONS
--------------------------------*/

function isInViewport(el) {
  const rect = el.getBoundingClientRect();
  return rect.top <= window.innerHeight - 50 && rect.bottom >= 0;
}

function animateElements() {
  const elements = document.querySelectorAll('.fade-down, .fade-up, .fade-in, .zoom-out');

  elements.forEach(el => {
    const delay = parseInt(el.getAttribute('data-delay')) || 0;

    if (isInViewport(el) && !el.classList.contains('show')) {
      setTimeout(() => {
        el.classList.add('show');
      }, delay);
    }
  });
}

window.addEventListener('load', animateElements);
window.addEventListener('scroll', animateElements);


/* -----------------------------
   HEADER SCROLL EFFECT
--------------------------------*/

function toggleScrolled() {
  const body = document.querySelector('body');
  const header = document.querySelector('#header');

  if (!header) return;

  if (
    header.classList.contains('scroll-up-sticky') ||
    header.classList.contains('sticky-top') ||
    header.classList.contains('fixed-top')
  ) {
    window.scrollY > 100
      ? body.classList.add('scrolled')
      : body.classList.remove('scrolled');
  }
}

document.addEventListener('scroll', toggleScrolled);
window.addEventListener('load', toggleScrolled);


/* -----------------------------
   MOBILE NAVIGATION
--------------------------------*/

const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');
const body = document.body;

if (mobileNavToggleBtn) {

  function mobileNavToggle() {

    body.classList.toggle('mobile-nav-active');

    const icon = mobileNavToggleBtn.querySelector('i');

    if (body.classList.contains('mobile-nav-active')) {
      icon.classList.remove('bi-list');
      icon.classList.add('bi-x');
    } else {
      icon.classList.remove('bi-x');
      icon.classList.add('bi-list');
    }
  }

  mobileNavToggleBtn.addEventListener('click', mobileNavToggle);
}


/* -----------------------------
   MOBILE DROPDOWN MENU
--------------------------------*/

document.querySelectorAll('.navmenu .toggle-dropdown').forEach(drop => {

  drop.addEventListener('click', function (e) {

    e.preventDefault();

    const parentLi = this.parentNode;

    parentLi.classList.toggle('active');

    this.nextElementSibling.classList.toggle('dropdown-active');

  });

});


/* -----------------------------
   PRELOADER
--------------------------------*/

const preloader = document.querySelector('#preloader');

if (preloader) {

  window.addEventListener('load', () => {

    preloader.remove();

  });

}


/* -----------------------------
   SCROLL TOP BUTTON
--------------------------------*/

const scrollTop = document.querySelector('.scroll-top');

function toggleScrollTop() {

  if (!scrollTop) return;

  window.scrollY > 100
    ? scrollTop.classList.add('active')
    : scrollTop.classList.remove('active');

}

if (scrollTop) {

  scrollTop.addEventListener('click', (e) => {

    e.preventDefault();

    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });

  });

}

window.addEventListener('load', toggleScrollTop);
document.addEventListener('scroll', toggleScrollTop);


/* -----------------------------
   PURE COUNTER
--------------------------------*/

if (typeof PureCounter !== "undefined") {
  new PureCounter();
}


/* -----------------------------
   FAQ TOGGLE
--------------------------------*/

document.querySelectorAll('.faq-item h3, .faq-item .faq-toggle').forEach(item => {

  item.addEventListener('click', () => {

    item.parentNode.classList.toggle('faq-active');

  });

});


/* -----------------------------
   SWIPER SLIDERS
--------------------------------*/

function initSwiper() {

  document.querySelectorAll(".init-swiper").forEach(function (swiperElement) {

    const configElement = swiperElement.querySelector(".swiper-config");

    if (!configElement) return;

    let config = JSON.parse(configElement.innerHTML.trim());

    new Swiper(swiperElement, config);

  });

}

window.addEventListener("load", initSwiper);


/* -----------------------------
   NAV MENU SCROLLSPY
--------------------------------*/

const navLinks = document.querySelectorAll('.navmenu a');

function navmenuScrollspy() {

  navLinks.forEach(link => {

    if (!link.hash) return;

    const section = document.querySelector(link.hash);

    if (!section) return;

    const position = window.scrollY + 200;

    if (
      position >= section.offsetTop &&
      position <= (section.offsetTop + section.offsetHeight)
    ) {

      document.querySelectorAll('.navmenu a.active')
        .forEach(el => el.classList.remove('active'));

      link.classList.add('active');

    } else {

      link.classList.remove('active');

    }

  });

}

window.addEventListener('load', navmenuScrollspy);
document.addEventListener('scroll', navmenuScrollspy);