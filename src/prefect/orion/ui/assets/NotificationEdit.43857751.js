import{d as h,b as y,Y as v,r as C,ax as N,e as x,o as c,f as r,w as u,g,h as f,a$ as E,a_ as b,q as k,ae as l,E as p,ad as B}from"./index.51b7df8a.js";import{u as I}from"./usePageTitle.5f1ff030.js";const q=h({__name:"NotificationEdit",async setup(T){let t,n;const i=y(),e=v("notificationId"),a=C({...([t,n]=N(()=>i.notifications.getNotification(e.value)),t=await t,n(),t)});async function d(s){try{await i.notifications.updateNotification(e.value,s),l.push(p.notifications())}catch(o){B("Error updating notification","error"),console.warn(o)}}function _(){l.push(p.notifications())}return I("Edit Notification"),(s,o)=>{const m=x("p-layout-default");return c(),r(m,null,{header:u(()=>[g(f(E))]),default:u(()=>[a.value?(c(),r(f(b),{key:0,notification:a.value,"onUpdate:notification":o[0]||(o[0]=w=>a.value=w),onSubmit:d,onCancel:_},null,8,["notification"])):k("",!0)]),_:1})}}});export{q as default};