suppressMessages(library(fixest))
d <- read.csv("../repo/data/promise_model_F5.csv", stringsAsFactors=FALSE, na.strings=c("","NA"))
n <- function(x) suppressWarnings(as.numeric(x))
d$country <- relevel(factor(d$country), ref="PL")
d$pilot <- as.integer(d$promise_status=="PILOT"); d$later <- n(d$n_later_reports)
d$general <- as.integer(d$category %in% c("general_ai","other")); d$spec2 <- as.integer(d$spec_final==2)
d$fid <- paste(d$country,d$firm); d$st <- ifelse(d$state=="yes",1,ifelse(d$state=="no",0,NA))
d$hold <- as.integer(grepl("samruk|baiterek", tolower(d$firm)))
X <- "country + pilot + general + later"
f <- function(y,rhs) as.formula(paste(y,"~",rhs,"| year"))
ms <- list(
 base   = feols(f("fulfilled",paste("spec2 + finance +",X)), d, cluster=~fid),
 nospec = feols(f("fulfilled",paste("finance +",X)), d, cluster=~fid),
 state  = feols(f("fulfilled",paste("spec2 + finance + st +",X)), d, cluster=~fid),
 size   = feols(f("fulfilled",paste("spec2 + finance + st + log_assets +",X)), d, cluster=~fid),
 old    = feols(f("fulfilled",paste("spec2 + finance +",X)), d[d$year<=2023,], cluster=~fid),
 later2 = feols(f("fulfilled",paste("spec2 + finance +",X)), d[d$later>=2,], cluster=~fid),
 nohold = feols(f("fulfilled",paste("spec2 + finance +",X)), d[d$hold==0,], cluster=~fid),
 anyc   = feols(f("I(1-dropped)",paste("spec2 + finance +",X)), d, cluster=~fid),
 fop    = feols(f("fulfilled_or_partial",paste("spec2 + finance +",X)), d, cluster=~fid))
etable(ms, keep=c("KZ","NL","^st$","finance","spec2"), digits=3, se.below=TRUE) |> print()
cat("\nN KZ/PL by subsample: old", table(d$country[d$year<=2023]), " later2", table(d$country[d$later>=2]), "\n")
cat("holdings rows:", sum(d$hold), "\n")
cat("\nfull by country x state:\n"); print(with(d, table(country, st, fulfilled, useNA="ifany")))
