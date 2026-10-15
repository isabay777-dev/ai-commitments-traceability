suppressMessages(library(fixest))
d <- read.csv("../repo/data/coded/kz_pl_firm_panel.csv", stringsAsFactors=FALSE)
d$st <- ifelse(d$state=="yes",1,ifelse(d$state=="no",0,NA))
d$fp <- ifelse(d$foreign_parent=="yes",1,ifelse(d$foreign_parent=="no",0,NA))
d$lchars <- log(d$chars); d$int <- d$ai_sentences/d$chars*1e5
cat("state values:\n"); print(table(d$country,d$state,useNA="ifany"))
cat("ai_any by country x state:\n"); print(aggregate(ai_any~country+state,d,function(x)c(n=length(x),m=round(mean(x),3))))
cat("mean log_assets / lchars by state:\n"); print(aggregate(cbind(log_assets,lchars)~country+state,d,mean))
for (cc in c("KZ","PL")) { s <- d[d$country==cc & !is.na(d$st),]
 cat("\n====",cc,"\n")
 m0 <- feols(ai_any~st|year, s, cluster=~firm)
 m1 <- feols(ai_any~st+lchars|year+sector_group, s, cluster=~firm)
 m2 <- feols(ai_any~st+lchars+log_assets|year+sector_group, s, cluster=~firm)
 m3 <- feols(ai_any~st+fp+lchars+log_assets|year+sector_group, s, cluster=~firm)
 m4 <- feols(int~st+lchars+log_assets|year+sector_group, s, cluster=~firm)
 etable(m0,m1,m2,m3,m4, se.below=TRUE, digits=3) |> print()
}
