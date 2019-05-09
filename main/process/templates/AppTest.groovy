package com.wanshifu

import com.wanshifu.framework.test.GroovySpockBaseTest
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.test.context.ActiveProfiles
import org.springframework.test.context.ContextConfiguration

/**
 * Title
 * Author jirenhe@wanshifu.com
 * Time 2018/6/4.
 * Version v1.0
 */
@ContextConfiguration(classes = [{{app_class_name}}Application])
@SpringBootTest(classes = [{{app_class_name}}Application])
@ActiveProfiles("test-case")
class {{app_class_name}}AppTest extends GroovySpockBaseTest {

}
