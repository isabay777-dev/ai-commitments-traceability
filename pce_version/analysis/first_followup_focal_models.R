# Exploratory first-report contrasts; no national or causal interpretation.
suppressPackageStartupMessages(library(fixest))
args <- commandArgs(trailingOnly=FALSE)
script <- sub('^--file=', '', args[grepl('^--file=',args)])
root <- normalizePath(file.path(dirname(script),'..'))
out <- file.path(root,'analysis','out')
d <- read.csv(file.path(out,'first_followup_analysis_data.csv'),stringsAsFactors=FALSE)
d <- subset(d,country %in% c('KZ','PL') & assessable %in% c(TRUE,'True','TRUE'))
d$kz <- as.integer(d$country=='KZ')
d$firm_id <- interaction(d$country,d$firm,drop=TRUE)
d$support_cell <- interaction(d$sector4,d$commitment_year,d$report_year_gap,drop=TRUE)
counts<-table(d$support_cell,d$country)
common<-rownames(counts)[counts[,'KZ']>0 & counts[,'PL']>0]
samples<-list(raw=d,one_year_gap=subset(d,report_year_gap==1),
 common_cells_raw=subset(d,support_cell %in% common),
 common_cells_FE=subset(d,support_cell %in% common))
forms<-list(raw=full~kz,one_year_gap=full~kz,common_cells_raw=full~kz,
 common_cells_FE=full~kz|support_cell)
results<-list();diagnostics<-character();support<-list()
for(name in names(samples)){
 dd<-samples[[name]]
 support[[name]]<-data.frame(model=name,N=nrow(dd),firms=length(unique(dd$firm_id)),
 KZ_N=sum(dd$country=='KZ'),PL_N=sum(dd$country=='PL'),
 KZ_firms=length(unique(dd$firm_id[dd$country=='KZ'])),PL_firms=length(unique(dd$firm_id[dd$country=='PL'])),
 observed_cells=length(unique(dd$support_cell)))
 fit<-tryCatch(feols(forms[[name]],data=dd,vcov=~firm_id,notes=FALSE),error=function(e)e)
 if(inherits(fit,'error')){results[[name]]<-data.frame(model=name,error=conditionMessage(fit));next}
 ct<-coeftable(fit);ci<-confint(fit)
 diagnostics<-c(diagnostics,paste(name,'dropped collinear terms:',paste(fit$collin.var,collapse=', ')))
 results[[name]]<-data.frame(model=name,term=rownames(ct),estimate_pp=100*ct[,1],se_pp=100*ct[,2],p=ct[,4],ci_lo_pp=100*ci[,1],ci_hi_pp=100*ci[,2],N=nobs(fit),firms=length(unique(dd$firm_id)))
}
for(name in names(results))write.csv(results[[name]],file.path(out,paste0('T_first_report_model_',name,'.csv')),row.names=FALSE)
write.csv(do.call(rbind,support),file.path(out,'T_first_report_model_support.csv'),row.names=FALSE)
writeLines(c('Common cells require both countries in the exact sector x commitment year x report-year-gap cell.','Cell FE contrast is exploratory and conditional on those sparse cells, not a national or like-for-like causal estimate.',diagnostics),file.path(out,'first_report_model_diagnostics.txt'))
writeLines(capture.output(sessionInfo()),file.path(out,'first_report_R_session.txt'))
