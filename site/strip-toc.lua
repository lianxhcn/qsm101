-- 原稿中的 [toc] 是发布平台占位符；网站使用 Quarto 的右侧目录。
function Para(el)
  if pandoc.utils.stringify(el) == "[toc]" then
    return {}
  end
end

-- 原稿的目录链接在网站上改指向可阅读的参考结果说明。
function Link(el)
  if el.target == "results/reference/" then
    el.target = "results/reference/README.md"
    return el
  end
end
