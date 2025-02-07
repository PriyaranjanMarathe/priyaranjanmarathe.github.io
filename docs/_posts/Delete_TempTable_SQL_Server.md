---
layout: "default"
title: Delete_TempTable_SQL_Server
comments: true
date: "2024-09-29"
categories: tils
---

`` IF Object_id('tempdb.dbo.#Temp_Table', 'U') IS NOT NULL
DROP TABLE #Temp_Table
