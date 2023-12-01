CREATE TABLE "USER" (
  "user_id" SERIAL PRIMARY KEY,
  "nickname" VARCHAR,
  "email" VARCHAR,
  "email_verified" VARCHAR,
  "picture" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "PURCHASED_PLAN" (
  "product_id" SERIAL PRIMARY KEY,
  "reference_name" VARCHAR,
  "price" INTEGER,
  "is_subscribed" BOOLEAN,
  "created_at" TIMESTAMP,
  "user_id" INTEGER REFERENCES "USER" ("user_id") ON DELETE CASCADE
);

CREATE TABLE "CATEGORY" (
  "category_id" SERIAL PRIMARY KEY,
  "category" VARCHAR,
  "image" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "COIN_BOT" (
  "bot_id" SERIAL PRIMARY KEY,
  "bot_name" VARCHAR,
  "keywords" VARCHAR[], 
  "sites" VARCHAR[],    
  "blacklist" VARCHAR[], 
  "alerts" VARCHAR[],   
  "analysis" VARCHAR[], 
  "top_stories" VARCHAR[], 
  "chart" VARCHAR,
  "image" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "KEYWORD" (
  "keyword_id" SERIAL PRIMARY KEY,
  "word" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "SITE" (
  "site_id" SERIAL PRIMARY KEY,
  "site_name" VARCHAR,
  "base_url" VARCHAR,
  "data_source_url" VARCHAR,
  "is_URL_complete" BOOLEAN,
  "main_container" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "BLACKLIST" (
  "blacklist_id" SERIAL PRIMARY KEY,
  "word" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "ALERT" (
  "alert_id" SERIAL PRIMARY KEY,
  "alert_name" VARCHAR,
  "alert_message" VARCHAR,
  "symbol" VARCHAR,
  "price" INTEGER,
  "created_at" TIMESTAMP
);

CREATE TABLE "TOP_STORY" (
  "top_story_id" SERIAL PRIMARY KEY,
  "story_date" VARCHAR,
  "summary" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "CATEGORY_NEWS_IMAGE" (
  "image_id" SERIAL PRIMARY KEY,
  "image" VARCHAR,
  "created_at" TIMESTAMP,
  "news_id" INTEGER REFERENCES "CATEGORY_NEWS" ("news_id") ON DELETE CASCADE
);

CREATE TABLE "CATEGORY_NEWS" (
  "news_id" SERIAL PRIMARY KEY,
  "news_date" VARCHAR,
  "summary" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "TOP_STORY_IMAGE" (
  "image_id" SERIAL PRIMARY KEY,
  "image" VARCHAR,
  "created_at" TIMESTAMP,
  "top_story_id" INTEGER REFERENCES "TOP_STORY" ("top_story_id") ON DELETE CASCADE
);

CREATE TABLE "ANALYSIS" (
  "analysis_id" SERIAL PRIMARY KEY,
  "analysis" VARCHAR,
  "images" VARCHAR,
  "created_at" TIMESTAMP
);

CREATE TABLE "ANALYSIS_IMAGE" (
  "image_id" SERIAL PRIMARY KEY,
  "image" VARCHAR,
  "created_at" TIMESTAMP,
  "analysis_id" INTEGER REFERENCES "ANALYSIS" ("analysis_id") ON DELETE CASCADE
);

CREATE TABLE "ANALYZED_ARTICLE" (
  "article_id" SERIAL PRIMARY KEY,
  "source" VARCHAR,
  "url" VARCHAR,
  "is_analyzed" BOOLEAN,
  "created_at" TIMESTAMP
);

CREATE TABLE "CHART" (
  "chart_id" SERIAL PRIMARY KEY,
  "support_1" INTEGER,
  "support_2" INTEGER,
  "support_3" INTEGER,
  "support_4" INTEGER,
  "resistance_1" INTEGER,
  "resistance_2" INTEGER,
  "resistance_3" INTEGER,
  "resistance_4" INTEGER,
  "created_at" TIMESTAMP
);

ALTER TABLE "PURCHASED_PLAN" ADD FOREIGN KEY ("user_id") REFERENCES "USER" ("user_id") ON DELETE CASCADE;

ALTER TABLE "CATEGORY" ADD FOREIGN KEY ("category_id") REFERENCES "COIN_BOT" ("bot_id");

ALTER TABLE "CHART" ADD FOREIGN KEY ("chart_id") REFERENCES "COIN_BOT" ("chart");

ALTER TABLE "ALERT" ADD FOREIGN KEY ("alert_id") REFERENCES "COIN_BOT" ("alerts");

ALTER TABLE "SITE" ADD FOREIGN KEY ("site_id") REFERENCES "COIN_BOT" ("sites");

ALTER TABLE "KEYWORD" ADD FOREIGN KEY ("keyword_id") REFERENCES "COIN_BOT" ("keywords");

ALTER TABLE "BLACKLIST" ADD FOREIGN KEY ("blacklist_id") REFERENCES "COIN_BOT" ("blacklist");

ALTER TABLE "ANALYZED_ARTICLE" ADD FOREIGN KEY ("article_id") REFERENCES "COIN_BOT" ("bot_id");

ALTER TABLE "CATEGORY_NEWS" ADD FOREIGN KEY ("news_id") REFERENCES "COIN_BOT" ("bot_id");

ALTER TABLE "ANALYSIS" ADD FOREIGN KEY ("analysis_id") REFERENCES "COIN_BOT" ("bot_id");

ALTER TABLE "TOP_STORY" ADD FOREIGN KEY ("top_story_id") REFERENCES "COIN_BOT" ("bot_id");

ALTER TABLE "CATEGORY_NEWS_IMAGE" ADD FOREIGN KEY ("news_id") REFERENCES "CATEGORY_NEWS" ("news_id");

ALTER TABLE "TOP_STORY_IMAGE" ADD FOREIGN KEY ("top_story_id") REFERENCES "TOP_STORY" ("top_story_id");

ALTER TABLE "ANALYSIS_IMAGE" ADD FOREIGN KEY ("analysis_id") REFERENCES "ANALYSIS" ("analysis_id");
