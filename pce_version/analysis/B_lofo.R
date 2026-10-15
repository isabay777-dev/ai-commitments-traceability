suppressMessages(library(fixest))
source_lines <- readLines("B_prelim.R"); eval(parse(text=source_lines[2:10]))
fit <- function(dd) { m <- feols(f("fulfilled",paste("spec2 + finance +",X)), dd, cluster=~fid); c(coef(m)["countryKZ"], se(m)["countryKZ"]) }
firms <- unique(d$fid[d$country %in% c("KZ","PL")])
r <- t(sapply(firms, function(ff) fit(d[d$fid!=ff,])))
r <- data.frame(dropped=firms, est=round(100*r[,1],1), se=round(100*r[,2],1)); r$t <- round(r$est/r$se,2)
print(r[order(r$est),], row.names=FALSE)
cat("\nrange est:", range(r$est), " min |t|:", min(abs(r$t)), "\n")
sam <- grepl("самрук_қазына|qazaqgaz|bank_centercredit", d$firm)
cat("drop Samruk-Kazyna+QazaqGaz+BCC:", round(100*fit(d[!sam,]),1), "n KZ", sum(d$country=="KZ" & !sam), "\n")
# firm-level aggregation: share fulfilled per firm, KZ vs PL
a <- aggregate(fulfilled~fid+country, d[d$country!="NL",], mean); print(aggregate(fulfilled~country,a,function(x)c(n=length(x),mean=round(mean(x),3))))
print(wilcox.test(fulfilled~droplevels(country), a, exact=FALSE))
